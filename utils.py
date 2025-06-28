import os
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf
import librosa
import librosa.display
from pydub import AudioSegment


def analyze_audio(filepath):
    y, sr = librosa.load(filepath, sr=None)
    dbfs = librosa.amplitude_to_db(np.abs(y), ref=np.max)
    return dbfs, sr, y


def plot_waveform(audio):
    if isinstance(audio, AudioSegment):
        y = np.array(audio.get_array_of_samples(), dtype=np.float32)
        if audio.channels == 2:
            y = y.reshape((-1, 2))
        # Normalize to [-1, 1] range (assuming 16-bit samples)
        y = y / 32768.0
        sr = audio.frame_rate
    else:
        y, sr = audio
    
    plt.figure(figsize=(14, 4))
    librosa.display.waveshow(y, sr=sr)
    plt.title("Waveform")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.tight_layout()
    plt.show()


def plot_dbfs(audio):
    if isinstance(audio, AudioSegment):
        y = np.array(audio.get_array_of_samples())
        if audio.channels == 2:
            y = y.reshape((-1, 2)).mean(axis=1)
        sr = audio.frame_rate
        dbfs = librosa.amplitude_to_db(np.abs(y), ref=np.max)
    else:
        dbfs, sr = audio
    
    plt.figure(figsize=(14, 4))
    times = np.linspace(0, len(dbfs)/sr, num=len(dbfs))
    plt.plot(times, dbfs, color='orange')
    plt.title("dBFS Profile")
    plt.xlabel("Time (s)")
    plt.ylabel("dBFS")
    plt.tight_layout()
    plt.show()


def recommend_silence_threshold(audio):
    # Sample audio to avoid memory issues with large files
    if isinstance(audio, AudioSegment):
        # Sample every 100ms to reduce memory usage
        sample_rate = 100  # ms
        samples = []
        for i in range(0, len(audio), sample_rate):
            chunk = audio[i:i+sample_rate]
            if len(chunk) > 0:
                samples.append(chunk.dBFS)
        dbfs_values = np.array(samples)
    else:
        dbfs_values = audio
    
    # Filter out -inf values
    dbfs_values = dbfs_values[dbfs_values > -np.inf]
    if len(dbfs_values) == 0:
        return -40  # Default fallback
    
    hist, bin_edges = np.histogram(dbfs_values, bins=50)
    peak_bin = bin_edges[np.argmax(hist)]
    return int(round(peak_bin - 5))  # Slightly below peak for better detection


def convert_to_pcm(input_path, output_dir=None):
    if output_dir is None:
        output_dir = os.path.dirname(input_path)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    wav_path = os.path.join(output_dir, base_name + "_temp.wav")
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", wav_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return wav_path


def convert_to_wav(input_path, output_dir):
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, base_name + ".wav")
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path


def convert_to_mp3(input_path, output_path):
    mp3_path = str(output_path.with_suffix(".mp3"))
    cmd = ["ffmpeg", "-y", "-i", str(input_path), "-codec:a", "libmp3lame", "-qscale:a", "2", mp3_path]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return mp3_path


def export_to_mp3(wav_path):
    mp3_path = wav_path.replace('.wav', '.mp3')
    cmd = ["ffmpeg", "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-qscale:a", "2", mp3_path]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return mp3_path
