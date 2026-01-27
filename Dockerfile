FROM python:3.12-slim

WORKDIR /app

# System deps (needed for mysql + cryptography)
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Expose backend port
EXPOSE 5000

# Run with gunicorn (PRODUCTION SAFE)
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "api:app"]
