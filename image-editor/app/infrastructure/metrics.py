from prometheus_client import Counter, Histogram

API_REQUESTS = Counter(
    "api_requests_total",
    "HTTP requests handled by the api service",
    ["method", "endpoint", "status"],
)
API_LATENCY = Histogram(
    "api_request_latency_seconds",
    "HTTP request latency in the api service",
    ["endpoint"],
)
TASKS_CREATED = Counter("api_tasks_created_total", "Tasks submitted for processing")
