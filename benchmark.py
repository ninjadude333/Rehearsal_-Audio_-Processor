import time
import librosa
import soundfile as sf
import numpy as np
import argparse
import os
import matplotlib.pyplot as plt


def analyze_rms_dbfs(y, sr, win_ms=100):
    win_size = int(sr * win_ms / 1000)
    y_mono = y if y.ndim == 1 else y.mean(axis=1)
    frames = y_mono[:len(y_mono) // win_size * win_size].reshape(-1, win_size)
    rms = np.sqrt(np.mean(frames**2, axis=1))
    dbfs = 20 * np.log10(rms + 1e-10)
    return dbfs, win_size


def detect_nonsilent_ranges(dbfs, win_size, sr, threshold_db=-30):
    is_loud = dbfs > threshold_db
    segments = []
    start = None
    for i, loud in enumerate(is_loud):
        if loud and start is None:
            start = i * win_size
        elif not loud and start is not None:
            end = i * win_size
            if end - start > 0:
                segments.append((start, end))
            start = None
    if start is not None:
        segments.append((start, len(dbfs) * win_size))
    return segments


def benchmark_trim(filepath, output_path, threshold_db, plot=False):
    print(f"[INFO] Benchmarking: {filepath}")
    start_all = time.time()

    # Load
    t0 = time.time()
    y, sr = librosa.load(filepath, sr=None, mono=False)
    load_time = time.time() - t0

    # Analyze
    t0 = time.time()
    dbfs, win_size = analyze_rms_dbfs(y, sr)
    analysis_time = time.time() - t0

    if plot:
        plt.figure(figsize=(14, 5))
        plt.plot(dbfs, label='dBFS')
        plt.axhline(threshold_db, color='red', linestyle='--', label='Threshold')
        plt.title("dBFS Profile")
        plt.xlabel("Frame Index")
        plt.ylabel("dBFS")
        plt.legend()
        plt.tight_layout()
        plt.show()

    # Detect segments
    t0 = time.time()
    segments = detect_nonsilent_ranges(dbfs, win_size, sr, threshold_db)
    detection_time = time.time() - t0

    if not segments:
        print("[WARN] No non-silent segments detected. Consider using a lower threshold (e.g. -45 dBFS).")
        return

    # Trim
    t0 = time.time()
    if y.ndim == 2:
        trimmed = np.concatenate([y[:, start:end] for start, end in segments], axis=1)
    else:
        trimmed = np.concatenate([y[start:end] for start, end in segments])
    trim_time = time.time() - t0

    # Export
    t0 = time.time()
    sf.write(output_path, trimmed.T if y.ndim == 2 else trimmed, sr)
    export_time = time.time() - t0

    total_time = time.time() - start_all

    print(f"[RESULTS] Load: {load_time:.2f}s | Analyze: {analysis_time:.2f}s | Detect: {detection_time:.2f}s | Trim: {trim_time:.2f}s | Export: {export_time:.2f}s | Total: {total_time:.2f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark and trim audio file using PCM analysis")
    parser.add_argument("input", help="Input audio file (mp3, wav, flac, etc.)")
    parser.add_argument("--threshold", type=float, default=-30.0, help="Silence threshold in dBFS")
    parser.add_argument("--output", help="Output trimmed file path")
    parser.add_argument("--plot-dbfs", action="store_true", help="Plot the dBFS profile with threshold")
    args = parser.parse_args()

    out = args.output or os.path.splitext(args.input)[0] + "_trimmed.wav"
    benchmark_trim(args.input, out, args.threshold, args.plot_dbfs)
