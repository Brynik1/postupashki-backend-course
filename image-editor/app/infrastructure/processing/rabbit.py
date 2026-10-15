import json

import pika

from app.config import Settings
from app.domain.task import Task
from app.domain.task_executor import TaskExecutor


class RabbitMQTaskExecutor(TaskExecutor):
    """Публикует задачу в RabbitMQ; ImageProcessor - отдельный сервис"""

    def __init__(self, settings: Settings) -> None:
        self._params = pika.URLParameters(settings.rabbit_url)
        self._queue = settings.task_queue

    def execute(self, task: Task) -> None:
        # подключение на одну публикацию; нагрузка небольшая,
        # это проще чем держать и лечить долговечное соединение
        connection = pika.BlockingConnection(self._params)
        try:
            channel = connection.channel()
            channel.queue_declare(queue=self._queue, durable=True)
            channel.basic_publish(
                exchange="",
                routing_key=self._queue,
                body=json.dumps({"task_id": task.task_id, "payload": task.payload}),
                properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent),
            )
        finally:
            connection.close()
