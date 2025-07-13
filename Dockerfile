# Используем официальный Python 3.11 slim
FROM python:3.11-slim

# Рабочая директория в контейнере
WORKDIR /app

# Копируем все файлы из текущей папки (где Dockerfile) в контейнер
COPY . /app

# Обновляем pip и устанавливаем зависимости из requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Запускаем бота (укажи тут файл, который запускает бота)
CMD ["python", "main.py"]
