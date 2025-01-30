# ===== Стадия 1: builder =====
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

# Отключаем создание .pyc и буфер вывода
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Устанавливаем необходимые системные пакеты
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt и устанавливаем зависимости ГЛОБАЛЬНО (без --user)
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# ===== Стадия 2: final =====
FROM python:3.11-slim-bookworm

WORKDIR /app

# Копируем глобальные пакеты (в /usr/local/...) из builder
COPY --from=builder /usr/local /usr/local

# Копируем всё остальное (код, конфиги, .env.example и т.п.)
COPY . .

# Создаём директории для данных и логов
RUN mkdir -p /app/data /app/logs

# Создаём пользователя и группу без привилегий
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /usr/sbin/nologin appuser

# Делаем пользователя владельцем /app с нужными правами
RUN chown -R appuser:appuser /app && \
    chmod -R 750 /app && \
    chmod -R 770 /app/logs && \
    chmod -R 770 /app/data

# Переключаемся на non-root пользователя
USER appuser

STOPSIGNAL SIGINT

# Запускаем бота
CMD ["python", "-u", "bot.py"]
