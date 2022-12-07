import os
from multiprocessing import cpu_count

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

bind = "0.0.0.0:5000"
workers = 3
loglevel = "info"
endpoint_agent = os.environ.get('INSTANA_AGENT_HOST', '127.0.0.1')

def on_starting(server):
    maximos_workers = cpu_count() * 2 + 1
    server.log.info ("*****************************")
    server.log.info ("Max num of workers..."+str(maximos_workers))
    server.log.info ("*****************************")

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

    # Instana
    trace.set_tracer_provider(TracerProvider(
        resource=Resource.create({
            ResourceAttributes.SERVICE_NAME: 'openapi',
        })
    ))

    # console mode
    #trace.get_tracer_provider().add_span_processor(
    #   BatchSpanProcessor(ConsoleSpanExporter())
    #)

    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint_agent}:4317",
                                            insecure=True, timeout=5))
    )
