FROM python:3.9-slim

WORKDIR /app

#install N-BaIoT dataset in kagglehub
RUN pip install --no-cache-dir scikit-learn pandas numpy joblib kagglehub

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all AI application files
COPY . .

# Create data directory for persistent logs
RUN mkdir -p /app/data

# Expose the port Flask will run on
EXPOSE 8080

# Health check (optional but good practice)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/stats', timeout=2)"

# Run the application
CMD ["python", "honeypot_proxy.py"]