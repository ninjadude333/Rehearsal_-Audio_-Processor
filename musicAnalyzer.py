import os
import csv
import logging
import requests
import hashlib
from pydub import AudioSegment
from utils import convert_to_pcm

try:
    import acoustid
    ACOUSTID_AVAILABLE = True
except ImportError:
    ACOUSTID_AVAILABLE = False

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

try:
    from shazamio import Shazam
    import asyncio
    SHAZAM_AVAILABLE = True
except ImportError:
    SHAZAM_AVAILABLE = False


class MusicAnalyzer:
    def __init__(self, api_key=None, reference_folder=None):
        self.api_key = api_key or "8XaBELgH"  # Free AcoustID key
        self.confidence_threshold = 0.5  # Even lower for covers
        self.reference_folder = reference_folder
        self.reference_signatures = {}
        if reference_folder:
            self._build_reference_database()
        
    def analyze_audio_file(self, filepath, output_dir=None, window_size=30):
        """Analyze audio file for song detection with timestamps"""
        logging.info(f"Analyzing audio file: {filepath}")
        
        # Convert to WAV if needed
        if not filepath.lower().endswith('.wav'):
            filepath = convert_to_pcm(filepath, output_dir)
            
        # Load audio
        audio = AudioSegment.from_wav(filepath)
        duration_ms = len(audio)
        
        results = []
        
        # Analyze in windows
        for start_ms in range(0, duration_ms, window_size * 1000):
            end_ms = min(start_ms + window_size * 1000, duration_ms)
            segment = audio[start_ms:end_ms]
            
            # Skip if segment too short
            if len(segment) < 10000:  # 10 seconds minimum
                continue
                
            timestamp = self._ms_to_timestamp(start_ms)
            detections = self._detect_song_segment(segment)
            
            if detections:
                for detection in detections:
                    results.append({
                        'timestamp': timestamp,
                        'song': detection['title'],
                        'artist': detection['artist'],
                        'confidence': detection['confidence'],
                        'method': detection.get('method', 'unknown')
                    })
            else:
                results.append({
                    'timestamp': timestamp,
                    'song': 'undetected',
                    'artist': '',
                    'confidence': 0.0,
                    'method': 'none'
                })
                
        return results
    
    def _detect_song_segment(self, segment):
        """Detect song using multiple methods"""
        detections = []
        
        # Method 1: Shazam API (best for actual songs)
        if SHAZAM_AVAILABLE:
            detections.extend(self._shazam_detect(segment))
            
        # Method 2: AcoustID (if available)
        if not detections and ACOUSTID_AVAILABLE:
            detections.extend(self._acoustid_detect(segment))
            
        # Method 3: Local reference matching
        if not detections and self.reference_signatures:
            detections.extend(self._reference_match(segment))
            
        # Method 4: Tempo analysis (fallback)
        if not detections and LIBROSA_AVAILABLE:
            detections.extend(self._tempo_detect(segment))
            
        return detections
    
    def _shazam_detect(self, segment):
        """Shazam detection using shazamio"""
        try:
            temp_path = "temp_segment.wav"
            segment.export(temp_path, format="wav")
            
            # Run async Shazam detection
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._async_shazam_detect(temp_path))
            loop.close()
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            return result
            
        except Exception as e:
            logging.info(f"Shazam failed: {e}")
            return []
    
    async def _async_shazam_detect(self, temp_path):
        """Async Shazam detection"""
        shazam = Shazam()
        result = await shazam.recognize(temp_path)
        
        detections = []
        if result and 'track' in result:
            track = result['track']
            title = track.get('title', 'Unknown')
            artist = track.get('subtitle', 'Unknown')
            
            detections.append({
                'title': title,
                'artist': artist,
                'confidence': 0.9,
                'method': 'shazam'
            })
            logging.info(f"Shazam detected: {artist} - {title}")
            
        return detections
    
    def _acoustid_detect(self, segment):
        """AcoustID detection (requires fpcalc)"""
        try:
            temp_path = "temp_segment.wav"
            segment.export(temp_path, format="wav")
            
            results = acoustid.match(self.api_key, temp_path)
            detections = []
            
            for score, recording_id, title, artist in results:
                if score >= self.confidence_threshold:
                    detections.append({
                        'title': title or 'Unknown',
                        'artist': artist or 'Unknown',
                        'confidence': score,
                        'method': 'acoustid'
                    })
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            return detections
            
        except Exception as e:
            logging.debug(f"AcoustID failed: {e}")
            return []
    
    def _tempo_detect(self, segment):
        """Enhanced audio analysis for covers"""
        if not LIBROSA_AVAILABLE:
            return []
            
        try:
            temp_path = "temp_segment.wav"
            segment.export(temp_path, format="wav")
            
            y, sr = librosa.load(temp_path)
            
            # Extract multiple features
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            tempo_val = float(tempo.item()) if hasattr(tempo, 'item') else float(tempo)
            
            # Chord progression (simplified)
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            chroma_mean = chroma.mean(axis=1)
            dominant_notes = chroma_mean.argsort()[-3:][::-1]  # Top 3 notes
            
            # Key estimation
            key_profiles = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            estimated_key = key_profiles[chroma_mean.argmax()]
            
            detections = []
            if 60 <= tempo_val <= 180:
                # Create signature from tempo + key + dominant notes
                signature = f"{estimated_key}_{int(tempo_val)}_{'-'.join(map(str, dominant_notes))}"
                
                confidence = min(0.7, tempo_val / 120)
                detections.append({
                    'title': f'Song_{signature}',
                    'artist': f'Key_{estimated_key}',
                    'confidence': confidence,
                    'method': 'audio_signature'
                })
                logging.info(f"Audio signature: {estimated_key} key, {tempo_val:.1f} BPM")
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            return detections
            
        except Exception as e:
            logging.debug(f"Audio analysis failed: {e}")
            return []
    
    def _build_reference_database(self):
        """Build signatures from reference songs"""
        if not LIBROSA_AVAILABLE or not os.path.exists(self.reference_folder):
            return
            
        logging.info(f"Building reference database from: {self.reference_folder}")
        
        for filename in os.listdir(self.reference_folder):
            if filename.lower().endswith(('.mp3', '.wav', '.flac', '.m4a')):
                filepath = os.path.join(self.reference_folder, filename)
                try:
                    # Load and analyze reference song
                    audio = AudioSegment.from_file(filepath)
                    # Take middle 30 seconds for signature
                    mid_point = len(audio) // 2
                    segment = audio[mid_point-15000:mid_point+15000]
                    
                    signature = self._extract_signature(segment)
                    if signature:
                        song_name = os.path.splitext(filename)[0]
                        self.reference_signatures[song_name] = signature
                        logging.info(f"Added reference: {song_name}")
                        
                except Exception as e:
                    logging.warning(f"Failed to process reference {filename}: {e}")
    
    def _extract_signature(self, segment):
        """Extract audio signature for matching"""
        try:
            temp_path = "temp_ref.wav"
            segment.export(temp_path, format="wav")
            
            y, sr = librosa.load(temp_path)
            
            # Extract features
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            tempo_val = float(tempo.item()) if hasattr(tempo, 'item') else float(tempo)
            
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            chroma_mean = chroma.mean(axis=1)
            
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=12)
            mfcc_mean = mfcc.mean(axis=1)
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            return {
                'tempo': tempo_val,
                'chroma': chroma_mean,
                'mfcc': mfcc_mean
            }
            
        except Exception as e:
            logging.debug(f"Signature extraction failed: {e}")
            return None
    
    def _reference_match(self, segment):
        """Match against reference database"""
        current_sig = self._extract_signature(segment)
        if not current_sig:
            return []
            
        best_match = None
        best_score = 0
        
        for song_name, ref_sig in self.reference_signatures.items():
            # Calculate similarity score
            tempo_diff = abs(current_sig['tempo'] - ref_sig['tempo']) / max(current_sig['tempo'], ref_sig['tempo'])
            tempo_score = max(0, 1 - tempo_diff)
            
            # Chroma similarity (chord progression)
            import numpy as np
            chroma_corr = np.corrcoef(current_sig['chroma'], ref_sig['chroma'])[0,1]
            chroma_score = max(0, chroma_corr) if not np.isnan(chroma_corr) else 0
            
            # MFCC similarity (timbre)
            mfcc_corr = np.corrcoef(current_sig['mfcc'], ref_sig['mfcc'])[0,1]
            mfcc_score = max(0, mfcc_corr) if not np.isnan(mfcc_corr) else 0
            
            # Combined score
            total_score = (tempo_score * 0.3 + chroma_score * 0.5 + mfcc_score * 0.2)
            
            if total_score > best_score and total_score > 0.6:  # Threshold for match
                best_score = total_score
                best_match = song_name
        
        if best_match:
            logging.info(f"Reference match: {best_match} (score: {best_score:.2f})")
            return [{
                'title': best_match,
                'artist': 'Cover',
                'confidence': best_score,
                'method': 'reference_match'
            }]
            
        return []
    
    def _feature_detect(self, segment):
        """Basic audio feature detection (placeholder for future)"""
        # Placeholder for tempo/key-based detection
        return []
    
    def _ms_to_timestamp(self, ms):
        """Convert milliseconds to MM:SS format"""
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def save_results_csv(self, results, output_path):
        """Save detection results to CSV"""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'song', 'artist', 'confidence', 'method'])
            writer.writeheader()
            writer.writerows(results)
        logging.info(f"Results saved to: {output_path}")
    
    def analyze_with_silence_detection(self, filepath, segments, output_dir):
        """Analyze specific segments from silence detection"""
        results = []
        audio = AudioSegment.from_wav(filepath)
        
        for i, (start_ms, end_ms) in enumerate(segments):
            segment = audio[start_ms:end_ms]
            timestamp = self._ms_to_timestamp(start_ms)
            
            detections = self._detect_song_segment(segment)
            
            if detections:
                for detection in detections:
                    results.append({
                        'segment': i + 1,
                        'timestamp': timestamp,
                        'duration': f"{(end_ms - start_ms) // 1000}s",
                        'song': detection['title'],
                        'artist': detection['artist'],
                        'confidence': detection['confidence'],
                        'method': detection.get('method', 'unknown')
                    })
            else:
                results.append({
                    'segment': i + 1,
                    'timestamp': timestamp,
                    'duration': f"{(end_ms - start_ms) // 1000}s",
                    'song': 'undetected',
                    'artist': '',
                    'confidence': 0.0,
                    'method': 'none'
                })
                
        return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Music Analysis Tool")
    parser.add_argument("input", help="Input audio file")
    parser.add_argument("--output", help="Output directory")
    parser.add_argument("--window", type=int, default=30, help="Analysis window size in seconds")
    parser.add_argument("--api_key", help="AcoustID API key")
    parser.add_argument("--references", help="Folder with reference songs to match against")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    
    # Check available detection methods
    methods = []
    if SHAZAM_AVAILABLE:
        methods.append('Shazam')
    if ACOUSTID_AVAILABLE:
        methods.append('AcoustID')
    if LIBROSA_AVAILABLE:
        methods.append('Tempo')
    
    if not methods:
        logging.error("No detection methods available. Install ShazamAPI, pyacoustid, or librosa")
        return
    
    logging.info(f"Available detection methods: {', '.join(methods)}")
    
    analyzer = MusicAnalyzer(api_key=args.api_key, reference_folder=args.references)
    output_dir = args.output or "./"
    
    logging.info(f"Analyzing: {args.input}")
    results = analyzer.analyze_audio_file(args.input, output_dir, args.window)
    
    if results:
        output_path = os.path.join(output_dir, "song_detection_results.csv")
        analyzer.save_results_csv(results, output_path)
        
        detected = sum(1 for r in results if r['song'] != 'undetected')
        logging.info(f"Analysis complete: {detected}/{len(results)} segments detected")
        print(f"\nResults saved to: {output_path}")
    else:
        logging.error("Analysis failed")


if __name__ == "__main__":
    main()