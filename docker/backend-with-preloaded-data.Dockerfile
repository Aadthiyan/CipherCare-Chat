FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install CyborgDB and sentence-transformers (for data loading)
RUN pip install --no-cache-dir cyborgdb sentence-transformers

# Copy application code
COPY backend/ .

# Create necessary directories
RUN mkdir -p /app/storage /app/logs /app/cyborgdb_data /app/data /app/scripts

# Copy patient data for pre-loading
COPY synthea_structured_cipercare.json /app/data/synthea_structured_cipercare.json

# Copy data loading script
COPY scripts/preload_data.py /app/scripts/preload_data.py

# PRE-LOAD PATIENT DATA INTO CYBORGDB
# This runs during Docker build, so data is baked into the image
RUN echo "Starting CyborgDB for data pre-load..." && \
    cyborgdb serve --port 8002 --data-dir /app/cyborgdb_data & \
    CYBORGDB_PID=$! && \
    sleep 10 && \
    echo "Loading patient data..." && \
    python /app/scripts/preload_data.py && \
    echo "Data loaded successfully!" && \
    kill $CYBORGDB_PID || true && \
    sleep 2

# Create supervisor config to run both services
RUN echo '[supervisord]' > /etc/supervisor/conf.d/supervisord.conf && \
    echo 'nodaemon=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'logfile=/app/logs/supervisord.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'pidfile=/var/run/supervisord.pid' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '[program:cyborgdb]' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'command=cyborgdb serve --port 8002 --data-dir /app/cyborgdb_data' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile=/app/logs/cyborgdb.err.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile=/app/logs/cyborgdb.out.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '[program:backend]' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'command=uvicorn backend.main:app --host 0.0.0.0 --port 8000' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile=/app/logs/backend.err.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile=/app/logs/backend.out.log' >> /etc/supervisor/conf.d/supervisord.conf

# Expose ports
EXPOSE 8000

# Health check (check backend)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run supervisor to manage both services
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
