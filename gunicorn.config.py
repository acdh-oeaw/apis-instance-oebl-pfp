import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor


def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

    resource = Resource.create(attributes={"service.name": "apis-oebl-pfp"})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    span_processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"))
    )
    trace.get_tracer_provider().add_span_processor(span_processor)
    DjangoInstrumentor().instrument(
        tracer_provider=provider,
        is_sql_commentor_enabled=True,
    )
    Psycopg2Instrumentor().instrument(
        tracer_provider=provider, skip_dep_check=True, enable_commenter=True
    )
