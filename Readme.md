# 🎵 Rehearsal Audio Processor

A Python-based command-line tool for efficiently processing long rehearsal or performance audio files.

## ✨ Features

- 🔊 **Trim**: Remove silent sections from a full audio recording
- ✂️ **Split**: Automatically split audio into multiple files based on detected silence
- 📊 **Waveform & dBFS Visualization**: Plot waveform and loudness profiles
- 🧠 **Smart Silence Threshold**: Analyze audio profile to recommend optimal silence detection threshold
- 🚀 **Auto Mode**: For batch runs—accepts all defaults, no prompts or popups
- 🔄 **Auto-Convert**: Automatically converts non-WAV files to WAV for optimal performance
- 💾 **Format Choice**: Choose to keep WAV output or convert back to original format
- 🧹 **Smart Cleanup**: Automatically manages temporary files during processing

## 🛠️ Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install FFmpeg:**
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg` or `sudo yum install ffmpeg`

## 🚀 Usage

### Song Finder (NEW!)

Find specific songs in rehearsal recordings:

```bash
# Find "Don't Stop Me Now" in rehearsal folder
python song_finder.py "C:\path\to\rehearsals" "Don't Stop Me Now"

# Or use batch file (Windows)
find_song.bat "C:\path\to\rehearsals" "Don't Stop Me Now"
```

Outputs CSV with:
- File name where song was found
- Time code when song starts (MM:SS)
- Detected song title and artist
- Detection confidence

### Single File Processing

```bash
python main.py "input.mp3" --mode split
```

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|----------|
| `input` | Input audio file path | Required |
| `--mode` | Processing mode: `split` or `trim` | Required |
| `--output` | Output directory | Same as input |
| `--silence_thresh` | Silence threshold in dBFS | Auto-detected |
| `--min_silence_len` | Minimum silence duration to detect (ms) | 1000 |
| `--keep_silence` | Padding around segments (ms) | 200 |
| `--plot` | Show interactive waveform plot | False |
| `--dbfs_plot` | Show dBFS profile plot | False |
| `--convert` | Convert input to WAV/PCM before processing | False |
| `--auto` | Accept auto-suggested threshold, suppress plots | False |
| `--mp3_out` | Convert final outputs to MP3 | False |

### Examples

**Trim and export to MP3 automatically:**
```bash
python main.py rehearsal.mp3 --mode trim --convert --auto --mp3_out
```

**Preview waveform:**
```bash
python main.py song.wav --plot
```

**Split with custom silence detection:**
```bash
python main.py live.wav --mode split --min_silence_len 1000 --silence_thresh -35
```

**Batch processing with auto mode:**
```bash
python main.py recording.mp3 --mode split --auto --convert --mp3_out --output ./processed/
```

## 🎛️ Processing Modes

### Split Mode
- Detects silence gaps in the audio
- Splits the recording into separate files for each non-silent segment
- Outputs: `filename_segment_1.wav`, `filename_segment_2.wav`, etc.

### Trim Mode
- Uses optimized split-and-stitch approach for faster processing
- Removes all silent sections from the audio
- Combines all non-silent segments into a single continuous file
- Output: `filename_trimmed.wav`

### Auto-Conversion
- Non-WAV files are automatically converted to WAV for optimal performance
- After processing, you can choose to keep WAV output or convert back to original format
- Temporary files are automatically cleaned up

## 📊 Visualization Features

**Waveform Plot (`--plot`):**
- Interactive visualization of the audio waveform
- Helps identify silence patterns visually

**dBFS Profile (`--dbfs_plot`):**
- Shows loudness levels over time
- Useful for understanding audio dynamics

## 🧠 Smart Silence Detection

The tool automatically analyzes your audio to recommend an optimal silence threshold:
- Calculates histogram of dBFS values
- Identifies the most common loudness level
- Suggests threshold based on audio characteristics
- Interactive prompt allows manual override (unless `--auto` is used)

## 📁 Supported Formats

**Input:** Any format supported by FFmpeg (MP3, WAV, FLAC, M4A, etc.)
**Output:** WAV (default) or MP3 (with `--mp3_out`)

## 🔧 Dependencies

- `pydub` - Core audio processing and silence detection
- `matplotlib` - Waveform and dBFS plotting
- `librosa` - Audio analysis and smart threshold recommendations
- `soundfile` - Audio file I/O
- `ffmpeg-python` - Audio format conversion
- `numpy` - Numerical processing
- `scipy` - Signal processing utilities
- `psutil` - System monitoring for benchmarks

## 🐳 Docker Support

```bash
# Build the container
docker build -t rehearsal-processor .

# Run with volume mount
docker run -v $(pwd):/app rehearsal-processor input.mp3 --mode split --auto
```

## 📈 Benchmarking

Performance test your audio processing with the included benchmark tool:

```bash
python benchmark.py "input.mp3" --output benchmark_results
```

The benchmark runs test scenarios with auto-conversion:
- **Auto-convert trim**: Automatically converts input and trims silence
- **Auto-convert split**: Automatically converts input and splits by silence

Results are saved to `benchmark_summary.csv` with metrics for duration, memory usage, output files, and total size.

## 📄 License

MIT License - see LICENSE file for details
