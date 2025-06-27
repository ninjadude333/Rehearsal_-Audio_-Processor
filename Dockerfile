FROM python:3.11-slim

# Install ffmpeg (required by pydub)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Default entrypoint
ENTRYPOINT ["python", "rehearsal_tool.py"]
