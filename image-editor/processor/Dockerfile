FROM python:3.12-slim

WORKDIR /usr/src/app

COPY processor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY processor ./processor

CMD ["python", "processor/main.py"]
