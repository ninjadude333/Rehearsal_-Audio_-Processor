FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg libchromaprint-tools && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Default entrypoint
ENTRYPOINT ["python", "main.py"]
