FROM python:3.12-slim

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

# Порт берётся из окружения (по умолчанию 8000) - как и всё остальное из app/config.py
ENV PORT="${PORT:-8000}"
CMD ["sh", "-c", "uvicorn app.main:app --host ${HOST:-0.0.0.0} --port ${PORT}"]
