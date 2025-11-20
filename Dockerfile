# Instagram Auto Publisher - Dockerfile
# Использует Python 3.11 на базе slim образа Debian

FROM python:3.11-slim

# Метаданные
LABEL maintainer="Iskander Chadoyev"
LABEL description="Instagram Auto Publisher - automated content management system"
LABEL version="2.0.0"

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt и устанавливаем Python зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Создаём директории
RUN mkdir -p /app/storys/video /app/storys/photo \
    /app/video_posts/clips /app/video_posts/igtv \
    /app/photo_posts /app/albums_posts /app/users_content

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Healthcheck
HEALTHCHECK --interval=60s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('db.db') else 1)"

# Команда запуска
CMD ["python", "app.py"]

