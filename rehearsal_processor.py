#!/usr/bin/env python3
import os
import argparse
import logging
import glob
from pathlib import Path
from pydub import AudioSegment, silence
from musicAnalyzer import MusicAnalyzer
from utils import recommend_silence_threshold, convert_to_pcm

class RehearsalProcessor:
    def __init__(self, songs_folder="./songs", min_silence_len=2000, auto_threshold=True):
        self.songs_folder = songs_folder
        self.min_silence_len = min_silence_len
        self.auto_threshold = auto_threshold
        self.analyzer = MusicAnalyzer(reference_folder=songs_folder)
        
    def find_audio_files(self, folder_path):
        """Find all audio files in folder"""
        audio_extensions = ['*.wav', '*.mp3', '*.flac', '*.m4a']
        audio_files = []
        
        for ext in audio_extensions:
            audio_files.extend(glob.glob(os.path.join(folder_path, ext)))
            audio_files.extend(glob.glob(os.path.join(folder_path, ext.upper())))
            
        return sorted(audio_files)
    
    def detect_song_segments(self, audio_file):
        """Detect song segments using silence detection"""
        logging.info(f"Processing: {os.path.basename(audio_file)}")
        
        # Convert to WAV if needed
        if not audio_file.lower().endswith('.wav'):
            audio_file = convert_to_pcm(audio_file)
            
        audio = AudioSegment.from_wav(audio_file)
        
        # Auto-detect silence threshold
        silence_thresh = recommend_silence_threshold(audio)
        logging.info(f"Using silence threshold: {silence_thresh} dBFS")
        
        # Detect segments between silences
        segments = silence.detect_nonsilent(
            audio, 
            min_silence_len=self.min_silence_len,
            silence_thresh=silence_thresh
        )
        
        logging.info(f"Found {len(segments)} song segments")
        return segments, audio
    
    def analyze_segments(self, audio, segments, output_file):
        """Analyze each segment for song detection"""
        results = []
        
        for i, (start_ms, end_ms) in enumerate(segments):
            segment = audio[start_ms:end_ms]
            duration_s = (end_ms - start_ms) / 1000
            
            # Skip very short segments
            if duration_s < 30:
                continue
                
            timestamp = f"{start_ms//60000:02d}:{(start_ms//1000)%60:02d}"
            
            logging.info(f"Analyzing segment {i+1}: {timestamp} ({duration_s:.1f}s)")
            
            # Use existing song detection
            detections = self.analyzer._detect_song_segment(segment)
            
            if detections:
                for detection in detections:
                    results.append({
                        'file': os.path.basename(output_file),
                        'segment': i + 1,
                        'start_time': timestamp,
                        'duration_s': int(duration_s),
                        'song': detection['title'],
                        'artist': detection['artist'],
                        'confidence': detection['confidence'],
                        'method': detection.get('method', 'unknown')
                    })
            else:
                results.append({
                    'file': os.path.basename(output_file),
                    'segment': i + 1,
                    'start_time': timestamp,
                    'duration_s': int(duration_s),
                    'song': 'undetected',
                    'artist': '',
                    'confidence': 0.0,
                    'method': 'none'
                })
                
        return results
    
    def process_folder(self, folder_path, output_dir="./output"):
        """Process all audio files in folder"""
        audio_files = self.find_audio_files(folder_path)
        
        if not audio_files:
            logging.error(f"No audio files found in {folder_path}")
            return
            
        logging.info(f"Found {len(audio_files)} audio files")
        
        os.makedirs(output_dir, exist_ok=True)
        all_results = []
        
        for audio_file in audio_files:
            try:
                segments, audio = self.detect_song_segments(audio_file)
                
                if segments:
                    results = self.analyze_segments(audio, segments, audio_file)
                    all_results.extend(results)
                    
            except Exception as e:
                logging.error(f"Failed to process {audio_file}: {e}")
                continue
        
        # Save combined results
        if all_results:
            output_path = os.path.join(output_dir, "rehearsal_analysis.csv")
            self.analyzer.save_results_csv(all_results, output_path)
            
            detected = sum(1 for r in all_results if r['song'] != 'undetected')
            logging.info(f"Analysis complete: {detected}/{len(all_results)} segments detected")
            print(f"\nResults saved to: {output_path}")
        else:
            logging.warning("No segments detected in any files")

def main():
    parser = argparse.ArgumentParser(description="Rehearsal Audio Processor - Batch process folder of rehearsal recordings")
    parser.add_argument("folder", help="Folder containing rehearsal audio files")
    parser.add_argument("--output", default="./output", help="Output directory for results")
    parser.add_argument("--songs", default="./songs", help="Reference songs folder")
    parser.add_argument("--min_silence", type=int, default=2000, help="Minimum silence length (ms)")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    
    processor = RehearsalProcessor(
        songs_folder=args.songs,
        min_silence_len=args.min_silence
    )
    
    processor.process_folder(args.folder, args.output)

if __name__ == "__main__":
    main()