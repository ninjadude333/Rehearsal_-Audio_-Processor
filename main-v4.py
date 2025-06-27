import argparse
import os
import time
import tempfile
import shutil
from pydub import AudioSegment, silence
from utils.audio_info import print_audio_info
from utils.plots import plot_waveform, plot_dbfs_profile
from utils.silence_analysis import analyze_dbfs_profile, recommend_silence_threshold
from utils.conversion import convert_to_wav_pcm, convert_to_mp3


def process_file(filepath, output_folder, mode, silence_thresh, min_silence_len, keep_silence, plot, dbfs_plot, auto, convert, mp3_out):
    start_time = time.time()
    filename = os.path.basename(filepath)
    name, ext = os.path.splitext(filename)

    if convert:
        filepath = convert_to_wav_pcm(filepath)
        filename = os.path.basename(filepath)
        name, ext = os.path.splitext(filename)

    print("[INFO] Processing file:", filepath)
    audio = AudioSegment.from_file(filepath)
    print_audio_info(audio, filepath)

    if plot and not auto:
        plot_waveform(audio, filename)
    if dbfs_plot and not auto:
        plot_dbfs_profile(audio, filename)

    if silence_thresh is None:
        silence_thresh = recommend_silence_threshold(audio)
        if not auto:
            inp = input(f"[INPUT] Suggested silence threshold: {silence_thresh} dBFS. Press Enter to accept or provide custom: ")
            if inp.strip():
                try:
                    silence_thresh = int(inp)
                except ValueError:
                    print("[WARN] Invalid input. Using suggested value.")

    if mode == 'split':
        print("[INFO] Detecting silence to split audio...")
        segments = silence.split_on_silence(audio, silence_thresh=silence_thresh, min_silence_len=min_silence_len, keep_silence=keep_silence)

        print(f"[INFO] Detected {len(segments)} segments")
        for i, segment in enumerate(segments, 1):
            out_path = os.path.join(output_folder, f"{name}_segment_{i}.wav")
            export_start = time.time()
            segment.export(out_path, format="wav")
            print(f"[INFO] Exported: {out_path} | Duration: {segment.duration_seconds:.2f}s | Time Taken: {time.time() - export_start:.2f}s")

    elif mode == 'trim':
        print("[INFO] Trimming audio by removing silence...")
        nonsilent_chunks = silence.detect_nonsilent(audio, silence_thresh=silence_thresh, min_silence_len=min_silence_len)
        combined = AudioSegment.empty()
        for start, end in nonsilent_chunks:
            combined += audio[start:end]

        out_path = os.path.join(output_folder, f"{name}_trimmed.wav")
        combined.export(out_path, format="wav")
        print(f"[INFO] Exported trimmed file: {out_path}")

    else:
        print("[ERROR] Unknown mode.")

    if mp3_out:
        print("[INFO] Converting outputs to MP3...")
        for file in os.listdir(output_folder):
            if file.endswith(".wav") and name in file:
                wav_path = os.path.join(output_folder, file)
                convert_to_mp3(wav_path)

    print(f"[INFO] Finished processing {filepath} in {time.time() - start_time:.2f} seconds")


def main():
    parser = argparse.ArgumentParser(description="Rehearsal Audio Processor")
    parser.add_argument("input", help="Path to input audio file")
    parser.add_argument("--mode", choices=['split', 'trim'], default='split', help="Processing mode")
    parser.add_argument("--output", default=None, help="Optional output folder")
    parser.add_argument("--silence_thresh", type=int, default=None, help="Silence threshold in dBFS")
    parser.add_argument("--min_silence_len", type=int, default=1000, help="Minimum silence length in ms")
    parser.add_argument("--keep_silence", type=int, default=200, help="Silence to keep around split segments")
    parser.add_argument("--plot", action='store_true', help="Show waveform plot")
    parser.add_argument("--dbfs_plot", action='store_true', help="Show dBFS loudness profile")
    parser.add_argument("--convert", action='store_true', help="Convert input file to WAV/PCM format before processing")
    parser.add_argument("--auto", action='store_true', help="Auto accept suggested threshold and suppress interactive prompts/plots")
    parser.add_argument("--mp3_out", action='store_true', help="Convert final output(s) to MP3")

    args = parser.parse_args()
    input_path = args.input
    output_path = args.output if args.output else os.path.dirname(input_path)

    print("[INFO] Starting rehearsal audio processing tool...")
    print("[INFO] Mode:", args.mode)
    print("[INFO] Input:", input_path)
    print("[INFO] Output:", output_path if args.output else "Same as input")

    process_file(
        input_path,
        output_path,
        args.mode,
        args.silence_thresh,
        args.min_silence_len,
        args.keep_silence,
        args.plot,
        args.dbfs_plot,
        args.auto,
        args.convert,
        args.mp3_out
    )


if __name__ == "__main__":
    main()