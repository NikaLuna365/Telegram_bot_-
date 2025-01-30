# Используем Python 3.9 (можно обновить до 3.10+)
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем оставшиеся файлы проекта
COPY . .

# Создаём папки для логов и данных, если их нет
RUN mkdir -p /app/data /app/logs

# Создаём нового пользователя внутри контейнера
RUN useradd -m appuser

# Даем права пользователю `appuser` только на папку с логами
RUN chown -R appuser:appuser /app/logs

# Запускаем контейнер под пользователем appuser
USER appuser

# Запускаем бота
CMD ["python", "bot.py"]
