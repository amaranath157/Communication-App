# ── Stage 1: Builder ────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Prevent .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies (for psycopg2, cryptography, mysqlclient, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a prefix directory
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: Production Image ────────────────────────────────────────────────
FROM python:3.12-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install only runtime system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libssl3 \
    libffi8 \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy project source
COPY . .

# Create a non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser \
    && chown -R appuser:appgroup /app

USER appuser

EXPOSE $PORT

# Run migrations, collect static, then start Daphne ASGI server
CMD sh -c "python manage.py migrate --noinput && \
           python manage.py collectstatic --noinput && \
           python manage.py createcachetable && \
           daphne -b 0.0.0.0 -p $PORT core.asgi:application"
