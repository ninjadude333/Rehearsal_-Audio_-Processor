#!/usr/bin/env python3
import os
import csv
import glob
import argparse
from pydub import AudioSegment, silence
from musicAnalyzer import MusicAnalyzer
from utils import recommend_silence_threshold, convert_to_pcm

def find_song_in_folder(folder_path, song_name, songs_folder="./songs"):
    """Find specific song in all audio files in folder"""
    # Find audio files
    audio_files = []
    for ext in ['*.wav', '*.mp3']:
        audio_files.extend(glob.glob(os.path.join(folder_path, ext)))
    
    if not audio_files:
        print(f"No audio files found in {folder_path}")
        return
    
    # Setup analyzer with reference songs
    analyzer = MusicAnalyzer(reference_folder=songs_folder)
    results = []
    
    for audio_file in audio_files:
        print(f"Processing: {os.path.basename(audio_file)}")
        print(f"Looking for: '{song_name}'")
        
        # Convert if needed
        if not audio_file.lower().endswith('.wav'):
            audio_file = convert_to_pcm(audio_file)
        
        audio = AudioSegment.from_wav(audio_file)
        silence_thresh = recommend_silence_threshold(audio)
        
        # Detect segments
        segments = silence.detect_nonsilent(audio, min_silence_len=2000, silence_thresh=silence_thresh)
        print(f"Found {len(segments)} segments:")
        
        # Check each segment for the target song
        for i, (start_ms, end_ms) in enumerate(segments):
            if (end_ms - start_ms) < 30000:  # Skip short segments
                continue
                
            segment = audio[start_ms:end_ms]
            detections = analyzer._detect_song_segment(segment)
            
            # Debug: show what was detected
            timestamp = f"{start_ms//60000:02d}:{(start_ms//1000)%60:02d}"
            if detections:
                for detection in detections:
                    print(f"  {timestamp}: {detection['title']} - {detection['artist']} ({detection['confidence']:.2f})")
            else:
                print(f"  {timestamp}: No detection")
            
            # Check if any detection matches our target song
            for detection in detections:
                title_match = song_name.lower() in detection['title'].lower() or detection['title'].lower() in song_name.lower()
                artist_match = song_name.lower() in detection['artist'].lower() or detection['artist'].lower() in song_name.lower()
                if title_match or artist_match:
                    results.append({
                        'file': os.path.basename(audio_file),
                        'time_code': timestamp,
                        'detected_song': detection['title'],
                        'artist': detection['artist'],
                        'confidence': detection['confidence']
                    })
    
    # Save results
    if results:
        output_file = f"{song_name.replace(' ', '_')}_detections.csv"
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['file', 'time_code', 'detected_song', 'artist', 'confidence'])
            writer.writeheader()
            writer.writerows(results)
        print(f"Found {len(results)} matches. Results saved to: {output_file}")
    else:
        print(f"No matches found for '{song_name}'")

def main():
    parser = argparse.ArgumentParser(description="Find specific song in rehearsal recordings")
    parser.add_argument("folder", help="Folder containing audio files")
    parser.add_argument("song", help="Song name to search for")
    parser.add_argument("--songs", default="./songs", help="Reference songs folder")
    args = parser.parse_args()
    
    find_song_in_folder(args.folder, args.song, args.songs)

if __name__ == "__main__":
    main()