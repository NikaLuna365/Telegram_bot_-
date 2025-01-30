# Используем официальный Python образ с конкретной версией (LTS)
FROM python:3.11-slim-bookworm AS builder

# Устанавливаем рабочий каталог
WORKDIR /app

# Настраиваем переменные окружения
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR 1

# Устанавливаем системные зависимости
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --user -r requirements.txt

# Финальный этап сборки
FROM python:3.11-slim-bookworm

WORKDIR /app

# Копируем установленные зависимости из builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app/requirements.txt .

# Копируем исходный код
COPY . .

# Создаем необходимые директории
RUN mkdir -p /app/data /app/logs

# Создаем непривилегированного пользователя и группу
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /sbin/nologin appuser

# Настраиваем права доступа
RUN chown -R appuser:appuser /app && \
    chmod -R 750 /app && \
    chmod -R 770 /app/logs && \
    chmod -R 770 /app/data

# Переключаемся на непривилегированного пользователя
USER appuser

# Убедимся, что скрипты в ~/.local/bin доступны
ENV PATH=/root/.local/bin:$PATH

# Используем правильный обработчик сигналов
STOPSIGNAL SIGINT

# Запускаем приложение
CMD ["python", "-u", "bot.py"]
