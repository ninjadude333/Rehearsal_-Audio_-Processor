import os
import argparse
import logging
import time
from pathlib import Path
from pydub import AudioSegment, silence
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

# Set up logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def print_audio_metadata(audio, filepath):
    duration_sec = len(audio) / 1000.0
    file_size = Path(filepath).stat().st_size / (1024 * 1024)
    logging.info(f"Duration: {duration_sec:.2f} seconds")
    logging.info(f"File size: {file_size:.2f} MB")
    try:
        sample_width = audio.sample_width * 8
        channels = audio.channels
        frame_rate = audio.frame_rate
        bitrate = frame_rate * channels * sample_width
        logging.info(f"Channels: {channels}, Frame Rate: {frame_rate}, Bitrate: {bitrate} bps")
    except Exception as e:
        logging.warning(f"Couldn't extract full audio metadata: {e}")

def plot_waveform(audio, title):
    samples = np.array(audio.get_array_of_samples())
    if audio.channels == 2:
        samples = samples.reshape((-1, 2))
        samples = samples.mean(axis=1)  # Convert to mono for simplicity

    step = max(1, len(samples) // 10000)
    samples = samples[::step]

    plt.figure(figsize=(15, 4))
    plt.plot(samples, linewidth=0.5)
    plt.title(f"Waveform: {title}")
    plt.xlabel("Sample index")
    plt.ylabel("Amplitude")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def plot_dbfs_profile(audio, title, step_ms=100):
    step_size = step_ms  # in milliseconds
    dBFS_vals = [audio[i:i+step_size].dBFS for i in range(0, len(audio), step_size)]

    plt.figure(figsize=(15, 4))
    plt.plot(np.arange(len(dBFS_vals)) * step_ms / 1000.0, dBFS_vals, linewidth=0.75)
    plt.title(f"dBFS Profile: {title}")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Loudness (dBFS)")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def process_file(filepath, output_dir, mode, silence_thresh=-40, min_silence_len=2000, keep_silence=500, show_plot=False, show_dbfs=False):
    start_time = time.time()
    logging.info(f"Processing file: {filepath}")
    audio = AudioSegment.from_file(filepath)
    print_audio_metadata(audio, filepath)

    if show_plot:
        plot_waveform(audio, Path(filepath).name)
    if show_dbfs:
        plot_dbfs_profile(audio, Path(filepath).name)

    filename = Path(filepath).stem
    output_dir.mkdir(parents=True, exist_ok=True)

    if mode == 'split':
        logging.info("Detecting silence to split audio...")
        chunks = silence.split_on_silence(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh,
            keep_silence=keep_silence
        )
        logging.info(f"Detected {len(chunks)} segments")
        for i, chunk in enumerate(chunks):
            split_start = time.time()
            out_path = output_dir / f"{filename}_segment_{i+1}.wav"
            chunk.export(out_path, format="wav")
            elapsed = time.time() - split_start
            chunk_duration = len(chunk) / 1000.0
            logging.info(f"Exported: {out_path} | Duration: {chunk_duration:.2f}s | Time Taken: {elapsed:.2f}s")

    elif mode == 'trim':
        logging.info("Detecting non-silent ranges to trim audio...")
        non_silent_ranges = silence.detect_nonsilent(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh
        )
        if not non_silent_ranges:
            logging.warning("No non-silent sections detected. Skipping.")
            return

        trimmed_audio = AudioSegment.empty()
        for start, end in non_silent_ranges:
            trimmed_audio += audio[start:end]
            logging.debug(f"Keeping range {start} to {end} ms")

        out_path = output_dir / f"{filename}_trimmed.wav"
        trimmed_audio.export(out_path, format="wav")
        trimmed_duration = len(trimmed_audio) / 1000.0
        logging.info(f"Exported trimmed file: {out_path} | Duration: {trimmed_duration:.2f}s")

    total_elapsed = time.time() - start_time
    logging.info(f"Finished processing {filepath} in {total_elapsed:.2f} seconds\n")

def process_folder(folder_path, output_dir, mode, silence_thresh, min_silence_len, keep_silence, show_plot, show_dbfs):
    audio_extensions = ['.wav', '.mp3', '.flac']
    all_files = list(Path(folder_path).rglob("*"))
    audio_files = [f for f in all_files if f.suffix.lower() in audio_extensions]

    logging.info(f"Found {len(audio_files)} audio files in folder: {folder_path}")
    for file in audio_files:
        out_dir = output_dir if output_dir else file.parent
        process_file(file, out_dir, mode, silence_thresh, min_silence_len, keep_silence, show_plot, show_dbfs)

def main():
    parser = argparse.ArgumentParser(description="Rehearsal Audio Processor")
    parser.add_argument("input", type=str, help="Input file or folder path")
    parser.add_argument("--mode", choices=['split', 'trim'], required=True, help="Choose 'split' or 'trim' mode")
    parser.add_argument("--output", type=str, default=None, help="Optional output folder")
    parser.add_argument("--silence_thresh", type=int, default=-40, help="Silence threshold in dBFS")
    parser.add_argument("--min_silence_len", type=int, default=2000, help="Minimum silence length in ms")
    parser.add_argument("--keep_silence", type=int, default=500, help="Padding silence around segments in ms")
    parser.add_argument("--plot", action="store_true", help="Display waveform plot before processing")
    parser.add_argument("--dbfs-profile", action="store_true", help="Display dBFS profile of audio")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output) if args.output else None

    logging.info("Starting rehearsal audio processing tool...")
    logging.info(f"Mode: {args.mode}")
    logging.info(f"Input: {input_path}")
    logging.info(f"Output: {output_dir if output_dir else 'Same as input'}")

    if input_path.is_file():
        final_output = output_dir or input_path.parent
        process_file(input_path, final_output, args.mode, args.silence_thresh, args.min_silence_len, args.keep_silence, args.plot, args.dbfs_profile)
    elif input_path.is_dir():
        process_folder(input_path, output_dir or input_path, args.mode, args.silence_thresh, args.min_silence_len, args.keep_silence, args.plot, args.dbfs_profile)
    else:
        logging.error("Invalid input path provided.")

if __name__ == "__main__":
    main()