"""ImageProcessor: потребляет задачи из RabbitMQ и коммитит результат через /commit"""

import base64
import json
import os
import time

import pika
import requests

RABBIT_URL = os.getenv("RABBIT_URL", "amqp://guest:guest@rabbitmq:5672/")
TASK_QUEUE = os.getenv("TASK_QUEUE", "processing_tasks")
API_URL = os.getenv("API_URL", "http://api:8000")

from filters import apply


def commit(task_id: str, image: bytes) -> None:
    resp = requests.post(
        f"{API_URL}/commit",
        json={"task_id": task_id, "image": base64.b64encode(image).decode("ascii")},
        timeout=10,
    )
    resp.raise_for_status()


def handle(channel, method, properties, body) -> None:
    try:
        message = json.loads(body)
        task_id = message["task_id"]
        payload = message["payload"]
        name = (payload.get("filter") or {}).get("name", "")
        parameters = (payload.get("filter") or {}).get("parameters") or {}
        image = base64.b64decode(payload["image"])
        processed = apply(name, image, parameters)
        commit(task_id, processed)
    except Exception as err:
        # кривую задачу не перевыставляем в очередь, чтобы не закрутиться в цикле
        print(f"processor: bad task dropped: {err}")
    channel.basic_ack(delivery_tag=method.delivery_tag)


def run() -> None:
    while True:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(RABBIT_URL))
            channel = connection.channel()
            channel.queue_declare(queue=TASK_QUEUE, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(TASK_QUEUE, on_message_callback=handle)
            channel.start_consuming()
        except Exception as err:
            print(f"processor: {err}, retrying in 3s")
            time.sleep(3)


if __name__ == "__main__":
    run()
