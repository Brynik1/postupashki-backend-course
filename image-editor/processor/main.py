"""ImageProcessor: потребляет задачи из RabbitMQ и коммитит результат через /commit"""

import base64
import json
import logging
import os
import time

import pika
import requests

from filters import apply
from metrics import FAILED_TASKS, FILTERS_USED, PROCESSING_TIME, expose_metrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("processor")

RABBIT_URL = os.getenv("RABBIT_URL", "amqp://guest:guest@rabbitmq:5672/")
TASK_QUEUE = os.getenv("TASK_QUEUE", "processing_tasks")
API_URL = os.getenv("API_URL", "http://api:8000")
COMMIT_SECRET = os.getenv("COMMIT_SECRET", "")


def _post_commit(body: dict) -> None:
    resp = requests.post(
        f"{API_URL}/commit",
        json=body,
        headers={"X-Processor-Token": COMMIT_SECRET},
        timeout=10,
    )
    resp.raise_for_status()


def commit_result(task_id: str, image: bytes) -> None:
    _post_commit(
        {"task_id": task_id, "image": base64.b64encode(image).decode("ascii")}
    )


def commit_failure(task_id: str, reason: str) -> None:
    _post_commit({"task_id": task_id, "error": reason})


def handle(channel, method, properties, body) -> None:
    # временная ошибка (api перезапускается, сеть шалит) - сообщение возвращаем
    # в очередь и пробуем позже; кривая задача - сообщаем api о failed и ack
    task_id = None
    try:
        message = json.loads(body)
        task_id = message["task_id"]
        payload = message["payload"]
        image = base64.b64decode(payload["image"])
        name = (payload.get("filter") or {}).get("name", "")
        parameters = (payload.get("filter") or {}).get("parameters") or {}
        with PROCESSING_TIME.labels(filter=name).time():
            processed = apply(name, image, parameters)
        commit_result(task_id, processed)
        FILTERS_USED.labels(filter=name).inc()
        channel.basic_ack(delivery_tag=method.delivery_tag)
        return
    except requests.HTTPError as err:
        status = err.response.status_code if err.response is not None else 0
        if status == 409:
            # таску уже закоммитили (дубликат из очереди) - это не ошибка
            log.info("task_id=%s already committed, skipping", task_id)
            channel.basic_ack(delivery_tag=method.delivery_tag)
        elif status >= 500:
            log.error("api returned %s for task_id=%s, requeued", status, task_id)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            time.sleep(1)
        else:
            # перманентный отказ API (401/422/...) - не крутим сообщение в цикле
            log.error("api rejected commit with %s for task_id=%s, dropped", status, task_id)
            channel.basic_ack(delivery_tag=method.delivery_tag)
        return
    except requests.RequestException as err:
        log.error("commit to api failed (%s), task_id=%s requeued", err, task_id)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        time.sleep(1)
        return
    except Exception as err:
        FAILED_TASKS.inc()
        log.error("task %s failed: %s", task_id, err)
        try:
            commit_failure(task_id or "", str(err))
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except requests.HTTPError as report_err:
            report_status = report_err.response.status_code if report_err.response is not None else 0
            if report_status in (404, 409):
                # таска неизвестна или уже готова - репортить некуда и незачем
                log.error("failure report rejected with %s for task_id=%s, dropped", report_status, task_id)
                channel.basic_ack(delivery_tag=method.delivery_tag)
            else:
                log.error("failure report rejected with %s for task_id=%s, requeued", report_status, task_id)
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                time.sleep(1)
        except requests.RequestException:
            # api недоступен - вернем сообщение, чтобы попытаться позже
            log.error("cannot report failure, task_id=%s requeued", task_id)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        return


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
            log.error("%s, retrying in 3s", err)
            time.sleep(3)


if __name__ == "__main__":
    expose_metrics(9100)
    run()
