import os
import argparse
import tempfile
import shutil
import logging
import time

from pydub import AudioSegment, silence
from utils import (
    analyze_audio,
    plot_waveform,
    plot_dbfs,
    recommend_silence_threshold,
    convert_to_pcm,
    export_to_mp3
)
from musicAnalyzer import MusicAnalyzer

def process_file(filepath, output_dir, mode, silence_thresh, min_silence_len, keep_silence, plot, dbfs_plot, convert, auto, mp3_out, song_detector=False):
    logging.info(f"Processing file: {filepath}")
    
    original_ext = os.path.splitext(filepath)[1].lower()
    converted_to_wav = False
    
    if original_ext != '.wav' or convert:
        logging.info("Converting to PCM WAV for better performance...")
        filepath = convert_to_pcm(filepath, output_dir)
        converted_to_wav = True

    audio = AudioSegment.from_file(filepath)
    duration = len(audio) / 1000
    size = os.path.getsize(filepath) / (1024 * 1024)
    logging.info(f"Duration: {duration:.2f} seconds")
    logging.info(f"File size: {size:.2f} MB")
    logging.info(f"Channels: {audio.channels}, Frame Rate: {audio.frame_rate}, Bitrate: {audio.frame_rate * audio.sample_width * 8 * audio.channels} bps")

    if dbfs_plot:
        plot_dbfs(audio)

    if plot:
        plot_waveform(audio)

    if silence_thresh is None:
        silence_thresh = recommend_silence_threshold(audio)
        logging.info(f"Recommended silence threshold: {silence_thresh} dBFS")
        if not auto:
            user_input = input(f"Use recommended threshold ({silence_thresh})? [Enter=yes / or type manual dBFS]: ")
            if user_input.strip():
                silence_thresh = float(user_input.strip())

    logging.info(f"Detecting silence to {mode} audio...")
    segments = silence.detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh, seek_step=1)
    logging.info(f"Detected {len(segments)} segments")

    if not segments:
        logging.warning("No non-silent segments found. Skipping file.")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if mode == "split":
        for i, (start, end) in enumerate(segments):
            segment = audio[start:end]
            out_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(filepath))[0]}_segment_{i+1}.wav")
            t0 = time.time()
            segment.export(out_path, format="wav")
            t1 = time.time()
            logging.info(f"Exported: {out_path} | Duration: {(end - start)/1000:.2f}s | Time Taken: {t1 - t0:.2f}s")
            if mp3_out:
                export_to_mp3(out_path)
    elif mode == "trim":
        # Use split approach for faster processing
        temp_files = []
        for i, (start, end) in enumerate(segments):
            segment = audio[start:end]
            temp_path = os.path.join(output_dir, f"temp_segment_{i}.wav")
            segment.export(temp_path, format="wav")
            temp_files.append(temp_path)
        
        # Stitch all parts together
        combined = AudioSegment.empty()
        for temp_file in temp_files:
            combined += AudioSegment.from_wav(temp_file)
        
        filename = os.path.basename(filepath).rsplit('.', 1)[0] + "_trimmed.wav"
        out_path = os.path.join(output_dir, filename)
        combined.export(out_path, format="wav")
        logging.info(f"Exported trimmed file: {out_path}")
        
        # Clean up temporary files
        for temp_file in temp_files:
            os.remove(temp_file)
        
        if mp3_out:
            export_to_mp3(out_path)
    
    # Ask user about output format if we converted to WAV
    if converted_to_wav and not auto:
        choice = input(f"Keep WAV output or convert to original format ({original_ext})? [w=WAV / o=original]: ").lower()
        if choice == 'o':
            if mode == "split":
                wav_files = [f for f in os.listdir(output_dir) if f.endswith('.wav') and 'segment' in f]
                for wav_file in wav_files:
                    wav_path = os.path.join(output_dir, wav_file)
                    if original_ext == '.mp3':
                        export_to_mp3(wav_path)
                        os.remove(wav_path)
            elif mode == "trim":
                if original_ext == '.mp3':
                    export_to_mp3(out_path)
                    os.remove(out_path)
    
    # Song detection if requested
    if song_detector:
        logging.info("Running song detection...")
        analyzer = MusicAnalyzer()
        if mode == "split" and segments:
            # Analyze each segment
            song_results = analyzer.analyze_with_silence_detection(filepath, segments, output_dir)
            csv_path = os.path.join(output_dir, "song_detection_segments.csv")
        else:
            # Analyze entire file
            song_results = analyzer.analyze_audio_file(filepath, output_dir)
            csv_path = os.path.join(output_dir, "song_detection_timeline.csv")
        
        if song_results:
            analyzer.save_results_csv(song_results, csv_path)
            detected = sum(1 for r in song_results if r['song'] != 'undetected')
            logging.info(f"Song detection: {detected}/{len(song_results)} detected")
    
    # Clean up temporary WAV file
    if converted_to_wav and '_temp.wav' in filepath:
        os.remove(filepath)


def main():
    parser = argparse.ArgumentParser(description="Rehearsal Audio Processor")
    parser.add_argument("input", help="Input audio file")
    parser.add_argument("--mode", choices=["split", "trim"], required=True)
    parser.add_argument("--output", help="Output directory")
    parser.add_argument("--silence_thresh", type=float, help="Silence threshold (dBFS)")
    parser.add_argument("--min_silence_len", type=int, default=1000, help="Minimum silence length (ms)")
    parser.add_argument("--keep_silence", type=int, default=200, help="Silence padding to keep (ms)")
    parser.add_argument("--plot", action="store_true", help="Plot waveform")
    parser.add_argument("--dbfs_plot", action="store_true", help="Plot dBFS profile")
    parser.add_argument("--convert", action="store_true", help="Convert input to WAV/PCM before processing")
    parser.add_argument("--auto", action="store_true", help="Auto accept recommended threshold")
    parser.add_argument("--mp3_out", action="store_true", help="Convert final output to MP3")
    parser.add_argument("--songDetector", action="store_true", help="Detect songs and output CSV")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    logging.info("Starting rehearsal audio processing tool...")
    logging.info(f"Mode: {args.mode}")
    logging.info(f"Input: {args.input}")

    output_dir = args.output or os.path.dirname(args.input)
    logging.info(f"Output: {output_dir if output_dir else 'Same as input'}")

    start_time = time.time()
    process_file(
        filepath=args.input,
        output_dir=output_dir,
        mode=args.mode,
        silence_thresh=args.silence_thresh,
        min_silence_len=args.min_silence_len,
        keep_silence=args.keep_silence,
        plot=args.plot if not args.auto else False,
        dbfs_plot=args.dbfs_plot if not args.auto else False,
        convert=args.convert,
        auto=args.auto,
        mp3_out=args.mp3_out,
        song_detector=args.songDetector
    )
    total = time.time() - start_time
    logging.info(f"Finished processing {args.input} in {total:.2f} seconds")


if __name__ == "__main__":
    main()
