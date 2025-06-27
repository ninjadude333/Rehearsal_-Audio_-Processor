# 🎵 Rehearsal Audio Processor

A Python-based open source CLI tool to process long band rehearsal audio recordings. Split or trim silence to isolate songs automatically.

## 🚀 Features
- **Split** audio into separate song files using silence detection.
- **Trim** silent gaps and output a single continuous file.
- **Batch processing** of entire folders of audio files.
- **Custom output directory** for processed files.

## 🛠 Installation
```bash
# Clone the repo
$ git clone https://github.com/yourname/rehearsal-processor.git
$ cd rehearsal-processor

# Build Docker container
$ docker build -t rehearsal-tool .
```

## 🧪 Usage
### With Docker
```bash
# Process a single file (split mode)
$ docker run -v $(pwd):/app rehearsal-tool input.wav --mode split

# Process a folder (trim mode)
$ docker run -v $(pwd):/app rehearsal-tool recordings/ --mode trim --output cleaned/
```

### Native Python
```bash
# Requires ffmpeg installed locally
$ pip install -r requirements.txt
$ python rehearsal_tool.py input.wav --mode split
```

## ⚙ Arguments
| Argument             | Description                              |
|----------------------|------------------------------------------|
| `input`              | Path to file or folder                   |
| `--mode`             | `split` or `trim`                        |
| `--output`           | Optional output folder                   |
| `--silence_thresh`   | Silence threshold in dBFS (default -40) |
| `--min_silence_len`  | Silence duration to trigger split (ms)  |
| `--keep_silence`     | Padding around segments (ms)            |

## 📦 Supported Formats
- `.wav`, `.mp3`, `.flac`

---

## 📄 License
[MIT License](LICENSE)
