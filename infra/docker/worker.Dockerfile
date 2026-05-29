FROM python:3.13-slim

# Worker image — will receive recon tool binaries in future layers (OCT-020+)
# For now: base Python + Dramatiq only. No recon tools yet.
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# Placeholder: future tool layers added here (subfinder, httpx, etc.)
# Each tool layer added via separate Dockerfile stage or RUN block
# Only the worker may execute external binaries (D-09)

CMD ["dramatiq", "app.workers.jobs", "--processes", "1", "--threads", "2"]
