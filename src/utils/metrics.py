from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time


# Define Prometheus metrics
# A counter for the total number of HTTP requests.
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "http_status"],
)

# A histogram for the latency of HTTP requests.
REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "Latency of HTTP requests in seconds",
    ["method", "endpoint"],
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    This class provides a middleware for collecting Prometheus metrics.
    """

    async def dispatch(self, request: Request, call_next):
        """
        This method is called for each request.

        Args:
            request (Request): The incoming request.
            call_next: The next middleware in the chain.

        Returns:
            The response.
        """
        start_time = time.time()

        # Process the request
        response = await call_next(request)

        # Record metrics after request is processed
        duration = time.time() - start_time
        endpoint = request.url.path

        # Increment the request count
        REQUEST_COUNT.labels(
            method=request.method, endpoint=endpoint, status=response.status_code
        ).inc()

        # Observe the request latency
        REQUEST_LATENCY.labels(method=request.method, endpoint=endpoint).observe(
            duration
        )

        return response


def setup_metrics(app: FastAPI):
    """
    Setup Prometheus metrics middleware and endpoint
    """

    # Add Prometheus middleware
    app.add_middleware(PrometheusMiddleware)

    @app.get("/TrhBVe_m5gg2002_E5VVqS", include_in_schema=False)
    def metrics():
        """
        This endpoint returns the latest Prometheus metrics.
        """
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
