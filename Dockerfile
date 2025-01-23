# Используем официальный образ Python
FROM python:3.9-slim

# Создадим рабочую директорию
WORKDIR /app

# Скопируем файлы requirements.txt в контейнер
COPY requirements.txt /app

# Установим зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Скопируем оставшиеся файлы в контейнер
COPY . /app

# Создадим папки data и logs внутри контейнера (на всякий случай)
RUN mkdir -p /app/data
RUN mkdir -p /app/logs

# Запускаем бота
CMD ["python", "bot.py"]
