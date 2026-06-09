"""OpenTelemetry tracing shared by all services and workers.

``init_tracing`` is a no-op when ``OTEL_EXPORTER_OTLP_ENDPOINT`` is unset, so
local runs and tests work without a collector. When set, spans are exported to
Tempo over OTLP/gRPC and SQLAlchemy + outbound HTTP are auto-instrumented.

Kafka is not auto-instrumented (confluent-kafka has no upstream instrumentor):
the outbox relay and the consumer loop propagate context manually via message
headers so a transfer traces end-to-end across the queue.
"""

import logging
import os

from opentelemetry import trace

logger = logging.getLogger(__name__)

_initialized = False


def init_tracing(service_name: str) -> None:
    """Wire up the global tracer provider once. Idempotent and safe to call
    from every service/worker entrypoint."""
    global _initialized
    if _initialized:
        return

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        logger.info("OTEL_EXPORTER_OTLP_ENDPOINT unset; tracing disabled")
        return

    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)

    # Outbound HTTP. Both clients are in play: chatbot/qa->mcp go through httpx
    # (mcp_client uses httpx.Client), chromadb's HttpClient also uses httpx;
    # requests covers anything left on the older client. Instrumenting both
    # propagates the trace context downstream (so mcp continues the same trace).
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
    except Exception:
        logger.exception("httpx instrumentation failed")
    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor

        RequestsInstrumentor().instrument()
    except Exception:
        logger.exception("requests instrumentation failed")

    # Database spans, hung under whatever request/consume span is active.
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        from shared.models import engine

        SQLAlchemyInstrumentor().instrument(engine=engine)
    except Exception:
        logger.exception("sqlalchemy instrumentation failed")

    _initialized = True
    logger.info("tracing enabled service=%s endpoint=%s", service_name, endpoint)


def get_tracer(name: str = "easyfocus"):
    return trace.get_tracer(name)
