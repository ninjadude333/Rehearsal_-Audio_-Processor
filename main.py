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

def process_file(filepath, output_dir, mode, silence_thresh, min_silence_len, keep_silence, plot, dbfs_plot, convert, auto, mp3_out):
    logging.info(f"Processing file: {filepath}")
    
    if convert:
        logging.info("Converting to PCM WAV...")
        filepath = convert_to_pcm(filepath)

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
        combined = AudioSegment.empty()
        for start, end in segments:
            combined += audio[start:end]
        filename = os.path.basename(filepath).rsplit('.', 1)[0] + "_trimmed.wav"
        out_path = os.path.join(output_dir, filename)
        combined.export(out_path, format="wav")
        logging.info(f"Exported trimmed file: {out_path}")
        if mp3_out:
            export_to_mp3(out_path)


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
        mp3_out=args.mp3_out
    )
    total = time.time() - start_time
    logging.info(f"Finished processing {args.input} in {total:.2f} seconds")


if __name__ == "__main__":
    main()
