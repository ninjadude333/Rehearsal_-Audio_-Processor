# Rehearsal Audio Processor

A Python-based command-line tool for efficiently processing long rehearsal or performance audio files.

## Features

- 🔊 **Trim**: Remove silent sections from a full audio recording.
- ✂️ **Split**: Automatically split audio into multiple files based on detected silence.
- 📊 **Waveform & dBFS Visualization**: Plot waveform and loudness profiles.
- 🧠 **Smart Silence Threshold**: Analyze audio profile to recommend optimal silence detection threshold.
- 🚀 **Auto Mode**: For batch runs—accepts all defaults, no prompts or popups.
- 🔄 **Convert Input**: Optionally convert any audio format to WAV/PCM for better performance.
- 💾 **Output to MP3**: Convert results back to MP3 after processing.

---

## Installation

```bash
pip install -r requirements.txt
```

Ensure `ffmpeg` is installed and available in your system PATH.

---

## Usage

```bash
python main.py "input.mp3" --mode split
```

### Optional Arguments

- `--output`: Set output directory.
- `--silence_thresh`: Set silence threshold in dBFS.
- `--min_silence_len`: Minimum silence duration to detect (ms).
- `--keep_silence`: Padding around segments.
- `--plot`: Plot waveform (interactive).
- `--dbfs_plot`: Plot dBFS profile.
- `--convert`: Convert input to WAV/PCM before processing.
- `--auto`: Accept auto-suggested threshold and suppress plots.
- `--mp3_out`: Convert final outputs to MP3.

### Examples

```bash
# Trim and export to MP3 automatically
python main.py rehearsal.mp3 --mode trim --convert --auto --mp3_out

# Preview waveform
python main.py song.wav --plot

# Split with silence detection
python main.py live.wav --mode split --min_silence_len 1000 --silence_thresh -35
```

---

## Requirements
See `requirements.txt` for complete list:
- `pydub`, `matplotlib`, `librosa`, `soundfile`, `ffmpeg-python`, `numpy`, `scipy`, `openpyxl`

---

## License
MIT License