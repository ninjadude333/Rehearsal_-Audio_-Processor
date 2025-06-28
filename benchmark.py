import os
import time
import psutil
import tracemalloc
import argparse
import logging
from pathlib import Path
from main import process_file
import csv

# Suppress logging during benchmark
logging.getLogger().setLevel(logging.ERROR)


def get_stats(start_time):
    duration = time.time() - start_time
    mem = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    return duration, mem


def run_test_case(name, input_path, output_dir, mode="trim"):
    print(f"\n[INFO] Running test: {name}")

    try:
        # Prepare output path
        test_output_dir = Path(output_dir) / name.replace(" ", "_").lower()
        test_output_dir.mkdir(parents=True, exist_ok=True)

        # Run process with fixed threshold (auto-converts internally)
        tracemalloc.start()
        start_time = time.time()
        process_file(
            filepath=str(input_path),
            output_dir=str(test_output_dir),
            mode=mode,
            silence_thresh=-35,  # Fixed threshold to avoid auto-detection
            min_silence_len=1000,
            keep_silence=200,
            plot=False,
            dbfs_plot=False,
            convert=False,
            auto=True,
            mp3_out=False
        )
        duration, mem = get_stats(start_time)
        tracemalloc.stop()

        # Count output files and total size
        output_files = list(test_output_dir.glob("*.wav"))
        total_size_mb = sum(f.stat().st_size for f in output_files) / (1024 * 1024)
        return {
            "Test Case": name,
            "Duration (s)": round(duration, 2),
            "Peak Memory (MB)": round(mem, 2),
            "Output Files": len(output_files),
            "Output Size (MB)": round(total_size_mb, 2)
        }
    except Exception as e:
        print(f"[ERROR] Test case '{name}' failed: {str(e)}")
        return {
            "Test Case": name,
            "Duration (s)": "FAILED",
            "Peak Memory (MB)": "FAILED",
            "Output Files": 0,
            "Output Size (MB)": 0
        }


def save_csv(results, output_dir):
    summary_path = Path(output_dir) / "benchmark_summary.csv"
    with open(summary_path, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    print(f"[INFO] Benchmark summary saved to {summary_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Path to input MP3 file")
    parser.add_argument("--output", help="Output base directory", default="benchmark_results")
    args = parser.parse_args()

    print(f"[INFO] Benchmarking: {args.input}")
    results = []

    results.append(run_test_case(
        name="Auto-convert trim",
        input_path=args.input,
        output_dir=args.output,
        mode="trim"
    ))

    results.append(run_test_case(
        name="Auto-convert split",
        input_path=args.input,
        output_dir=args.output,
        mode="split"
    ))

    save_csv(results, args.output)


if __name__ == '__main__':
    main()
