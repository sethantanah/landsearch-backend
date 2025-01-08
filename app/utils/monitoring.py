import time
import threading
from functools import wraps
from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest

# Metrics Setup
OPERATION_COUNTER = Counter(
    "pinecone_operations_total",
    "Total number of Pinecone operations",
    ["operation_type", "status"],
)
OPERATION_LATENCY = Histogram(
    "pinecone_operation_latency_seconds",
    "Latency of Pinecone operations",
    ["operation_type"],
)


# Rate Limiting
class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""

    def __init__(self, rate: float, burst: int):
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        with self._lock:
            now = time.time()
            time_passed = now - self.last_update
            self.tokens = min(self.burst, self.tokens + time_passed * self.rate)
            self.last_update = now

            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False


# Monitoring and Metrics Decorator
def monitor_operation(operation_type: str):
    """Decorator to monitor operations with metrics."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                OPERATION_COUNTER.labels(
                    operation_type=operation_type, status="success"
                ).inc()
                return result
            except Exception:
                OPERATION_COUNTER.labels(
                    operation_type=operation_type, status="failure"
                ).inc()
                raise
            finally:
                OPERATION_LATENCY.labels(operation_type=operation_type).observe(
                    time.time() - start_time
                )

        return wrapper

    return decorator


class MetricsManager:
    """Manager class for Prometheus metrics to avoid registration conflicts."""

    def __init__(self):
        # Create a custom registry
        self.registry = CollectorRegistry()

        # Initialize metrics with custom registry
        self.request_counter = Counter(
            name="app_http_requests_total",  # Changed name to avoid conflicts
            documentation="Total HTTP requests",
            labelnames=["method", "endpoint", "status"],
            registry=self.registry,  # Use custom registry
        )

        self.request_latency = Histogram(
            name="app_http_request_duration_seconds",  # Changed name to avoid conflicts
            documentation="HTTP request latency",
            labelnames=["method", "endpoint"],
            registry=self.registry,  # Use custom registry
        )

        self.error_counter = Counter(
            name="app_error_total",  # Changed name to avoid conflicts
            documentation="Total number of errors",
            labelnames=["error_type"],
            registry=self.registry,  # Use custom registry
        )

    def increment_request_count(self, method: str, endpoint: str, status: str) -> None:
        """Increment the request counter."""
        self.request_counter.labels(
            method=method, endpoint=endpoint, status=status
        ).inc()

    def observe_request_latency(
        self, method: str, endpoint: str, duration: float
    ) -> None:
        """Record request duration."""
        self.request_latency.labels(method=method, endpoint=endpoint).observe(duration)

    def increment_error_count(self, error_type: str) -> None:
        """Increment the error counter."""
        self.error_counter.labels(error_type=error_type).inc()

    def get_metrics(self) -> bytes:
        """Generate metrics output."""
        return generate_latest(self.registry)
