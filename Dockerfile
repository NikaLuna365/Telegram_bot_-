# ===== Стадия 1: builder =====
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

# Отключаем .pyc-файлы и буфер вывода Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Устанавливаем нужные системные зависимости (например, gcc, python3-dev — если нужно что-то компилировать)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# 1) Создаём виртуальное окружение
RUN python -m venv /app/venv

# 2) Настраиваем окружение, чтобы при RUN командах в builder
#    использовалась pip из venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# 3) Копируем requirements.txt и устанавливаем зависимости в /app/venv
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# ===== Стадия 2: final =====
FROM python:3.11-slim-bookworm

WORKDIR /app

# Копируем только виртуальное окружение из builder
COPY --from=builder /app/venv /app/venv

# Настраиваем ENV, чтобы при запуске контейнера использовался python/pip из venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Копируем остальной код (bot.py, .env.example и пр.)
COPY . .

# Создаём директории для данных и логов
RUN mkdir -p /app/data /app/logs

# Создаём непривилегированного пользователя и группу
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /usr/sbin/nologin appuser

# Настраиваем права
RUN chown -R appuser:appuser /app && \
    chmod -R 750 /app && \
    chmod -R 770 /app/logs && \
    chmod -R 770 /app/data

# Переключаемся на non-root пользователя
USER appuser

# Корректная обработка SIGINT
STOPSIGNAL SIGINT

# Запускаем бота
CMD ["python", "-u", "bot.py"]
