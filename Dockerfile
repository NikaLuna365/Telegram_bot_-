# ===== Стадия 1: builder =====
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

# Отключаем создание .pyc и буфер вывода
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Устанавливаем системные зависимости (если нужно что-то компилировать)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Создаём виртуальное окружение в /opt/venv
RUN python -m venv /opt/venv

# Активируем это окружение: в builder-слое pip указывает в /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Копируем список зависимостей и устанавливаем их в venv
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# ===== Стадия 2: final =====
FROM python:3.11-slim-bookworm

WORKDIR /app

# Копируем виртуальное окружение из builder
COPY --from=builder /opt/venv /opt/venv

# Активируем venv в финальном слое
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Создаём непривилегированного пользователя
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /usr/sbin/nologin appuser

# Копируем весь проект
COPY . .

# Создаём папки для данных и логов + даём права appuser
RUN mkdir -p /app/data /app/logs && \
    chown -R appuser:appuser /app && \
    chmod -R 750 /app && \
    chmod -R 770 /app/logs /app/data

# Запускаем контейнер под пользователем appuser
USER appuser

STOPSIGNAL SIGINT

# Запуск бота
CMD ["python", "bot.py"]
