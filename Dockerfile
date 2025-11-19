#root/Dockerfile
# Stage 1: build dependencies
FROM python:3.12-slim AS builder

# Set basic env variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Set minimum system deps for Playwright
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        git \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements
COPY requirements.txt dev-requirements.txt ./

# Create a separate venv to copy to stage run for convenience
RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r dev-requirements.txt

# Install playwright + chromium (used for both test & run)
RUN . /opt/venv/bin/activate && \
    python -m playwright install --with-deps chromium


# Stage 2: runtime image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy venv
COPY --from=builder /opt/venv /opt/venv

# Cài thêm deps hệ thống cần cho Playwright runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libnss3 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libxkbcommon0 \
        libdrm2 \
        libgbm1 \
        libasound2 \
        fonts-liberation \
        libgtk-3-0 \
        libx11-xcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libxcb1 \
        libxext6 \
        libegl1 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy source code into image
COPY . /app

# Create var folder for DB, logs, artifacts
RUN mkdir -p /app/var && \
    mkdir -p /app/var/artifacts /app/var/reports /app/var/app_db

# HTTP
EXPOSE 8000

# Default environment variables (can be overridden)
ENV AUTOSUITE_API_KEY_ENABLED="false" \
    AUTOSUITE_DB_URL="sqlite:///./var/app.db" \
    AUTOSUITE_DRIVER="playwright" \
    AUTOSUITE_EXECUTOR_MAX_WORKERS="1" \
    AUTOSUITE_ARTIFACTS_DIR="./var/artifacts" \
    AUTOSUITE_REPORTS_DIR="./var/reports"

# Command to run FastAPI with uvicorn
CMD ["uvicorn", "service.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

