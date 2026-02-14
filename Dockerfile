# Dockerfile for Plex Telegram Bot
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bot/ bot/
COPY scripts/ scripts/
COPY docs/ docs/
COPY CLAUDE.md .

# Make scripts executable
RUN chmod +x scripts/api-call scripts/recycle-bin

# Add scripts to PATH
ENV PATH="/app/scripts:${PATH}"

# Run as non-root user
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Start bot
CMD ["python", "-m", "bot.main"]
