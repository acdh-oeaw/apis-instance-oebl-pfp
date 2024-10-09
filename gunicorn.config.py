from opentelemetry.instrumentation.django import DjangoInstrumentor


def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

    DjangoInstrumentor().instrument()
