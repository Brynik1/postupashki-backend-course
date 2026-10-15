from prometheus_client import Counter, Histogram, start_http_server

PROCESSING_TIME = Histogram(
    "processor_task_processing_seconds",
    "Time spent processing one task (filter included)",
    ["filter"],
)
FILTERS_USED = Counter(
    "processor_filters_used_total",
    "Filters applied by the processor",
    ["filter"],
)
FAILED_TASKS = Counter("processor_failed_tasks_total", "Tasks the processor could not handle")


def expose_metrics(port: int = 9100) -> None:
    start_http_server(port)
