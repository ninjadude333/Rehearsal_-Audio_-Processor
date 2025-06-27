import argparse
import os
import time
import tempfile
import numpy as np
import matplotlib.pyplot as plt
from pydub import AudioSegment, silence
from scipy.io import wavfile


def analyze_audio(file_path):
    audio = AudioSegment.from_file(file_path)
    duration = len(audio) / 1000.0  # in seconds
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    bitrate = audio.frame_rate * audio.frame_width * audio.channels * 8

    print(f"[INFO] Duration: {duration:.2f} seconds")
    print(f"[INFO] File size: {size_mb:.2f} MB")
    print(f"[INFO] Channels: {audio.channels}, Frame Rate: {audio.frame_rate}, Bitrate: {bitrate} bps")
    return audio


def plot_waveform(audio, title):
    samples = np.array(audio.get_array_of_samples())
    plt.figure(figsize=(12, 4))
    plt.plot(samples[:10000])
    plt.title(f"Waveform: {title}")
    plt.xlabel("Sample index")
    plt.ylabel("Amplitude")
    plt.tight_layout()
    plt.show()


def plot_dbfs_profile(audio, title):
    chunk_ms = 100
    chunks = [audio[i:i+chunk_ms] for i in range(0, len(audio), chunk_ms)]
    dbfs = [chunk.dBFS for chunk in chunks]

    times = np.linspace(0, len(audio) / 1000, num=len(dbfs))
    plt.figure(figsize=(12, 4))
    plt.plot(times, dbfs)
    plt.title(f"dBFS Profile: {title}")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Loudness (dBFS)")
    plt.tight_layout()
    plt.show()


def detect_silence_threshold(audio):
    chunk_ms = 100
    dbfs_values = [audio[i:i+chunk_ms].dBFS for i in range(0, len(audio), chunk_ms)]
    dbfs_array = np.array(dbfs_values)
    recommended = np.percentile(dbfs_array[~np.isinf(dbfs_array)], 15)
    print(f"[INFO] Suggested silence threshold (15th percentile): {recommended:.2f} dBFS")
    manual = input("Enter silence threshold (Press Enter to accept suggested): ")
    selected = float(manual) if manual.strip() else round(recommended, 2)
    print(f"[INFO] Selected silence threshold: {selected} dBFS")
    return selected


def trim_silence(audio, threshold, min_len=1000, keep_silence=200):
    non_silent = silence.detect_nonsilent(audio, min_silence_len=min_len,
                                          silence_thresh=threshold, seek_step=1)
    print(f"[INFO] Detected {len(non_silent)} sound segments")

    combined = AudioSegment.empty()
    for idx, (start, end) in enumerate(non_silent):
        chunk = audio[start:end]
        combined += chunk + AudioSegment.silent(duration=keep_silence)
    return combined


def split_audio(audio, threshold, min_len=1000, keep_silence=200, out_prefix="segment"):
    chunks = silence.split_on_silence(audio, silence_thresh=threshold,
                                      min_silence_len=min_len, keep_silence=keep_silence)
    print(f"[INFO] Detected {len(chunks)} segments")
    return chunks


def save_audio(audio, path):
    audio.export(path, format="wav")
    print(f"[INFO] Exported: {path}")


def process_file(path, mode, out_folder=None, silence_thresh=None, min_len=1000, keep_silence=200, plot=False, dbfs=False):
    print("[INFO] Starting rehearsal audio processing tool...")
    print(f"[INFO] Mode: {mode}")
    print(f"[INFO] Input: {path}")
    out_folder = out_folder or os.path.dirname(path)
    print(f"[INFO] Output: {out_folder}")

    audio = analyze_audio(path)
    title = os.path.basename(path)
    
    if plot:
        plot_waveform(audio, title)

    if dbfs:
        plot_dbfs_profile(audio, title)

    threshold = silence_thresh if silence_thresh is not None else detect_silence_threshold(audio)

    start = time.time()

    if mode == "trim":
        trimmed = trim_silence(audio, threshold, min_len, keep_silence)
        out_path = os.path.join(out_folder, os.path.splitext(os.path.basename(path))[0] + "-trimmed.wav")
        save_audio(trimmed, out_path)

    elif mode == "split":
        segments = split_audio(audio, threshold, min_len, keep_silence)
        for i, chunk in enumerate(segments, 1):
            filename = f"{os.path.splitext(os.path.basename(path))[0]}_segment_{i}.wav"
            save_audio(chunk, os.path.join(out_folder, filename))

    else:
        print("[ERROR] Invalid mode specified.")

    print(f"[INFO] Finished processing in {time.time() - start:.2f} seconds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rehearsal Audio Processor")
    parser.add_argument("input", help="Input audio file path")
    parser.add_argument("--mode", choices=["trim", "split"], default="split", help="Operation mode")
    parser.add_argument("--output", help="Output folder path")
    parser.add_argument("--silence_thresh", type=float, help="Silence threshold in dBFS")
    parser.add_argument("--min_silence_len", type=int, default=1000, help="Minimum silence length in ms")
    parser.add_argument("--keep_silence", type=int, default=200, help="Keep silence around segments in ms")
    parser.add_argument("--plot", action="store_true", help="Plot waveform")
    parser.add_argument("--dbfs", action="store_true", help="Plot dBFS profile")
    args = parser.parse_args()

    process_file(args.input, args.mode, args.output, args.silence_thresh,
                 args.min_silence_len, args.keep_silence, args.plot, args.dbfs)
