FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Make startup script executable
RUN chmod +x start.sh

# Create data directories
RUN mkdir -p data/raw data/processed data/external experiments/results experiments/logs

EXPOSE 8000

# Generate data (if missing) then start API
CMD ["./start.sh"]