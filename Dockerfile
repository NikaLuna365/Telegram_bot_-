# ===== Стадия 1: builder =====
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# ===== Стадия 2: final =====
FROM python:3.11-slim-bookworm

WORKDIR /app

# Копируем установленные пакеты (папки /usr/local) из builder-образа
COPY --from=builder /usr/local /usr/local

# Копируем наш код
COPY . .

# Создаём пользователя
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /sbin/nologin appuser

RUN mkdir -p /app/data /app/logs && \
    chown -R appuser:appuser /app && \
    chmod -R 750 /app

USER appuser

STOPSIGNAL SIGINT

CMD ["python", "-u", "bot.py"]
