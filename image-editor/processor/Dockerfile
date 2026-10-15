FROM python:3.12-slim

WORKDIR /usr/src/app

COPY processor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY processor ./processor

# без этого docker logs не видит python-логи (stdout не tty и буферизуется)
ENV PYTHONUNBUFFERED=1

CMD ["python", "processor/main.py"]
