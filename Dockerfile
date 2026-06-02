FROM python:3.12-slim

LABEL maintainer="tomer.klein@gmail.com"

ENV PYTHONIOENCODING=utf-8 \
    LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/decompose

COPY decompose/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY decompose/ .

RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /opt/decompose
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8080/ || exit 1

ENTRYPOINT ["python3", "decompose.py"]
