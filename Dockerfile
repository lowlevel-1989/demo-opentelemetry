FROM ubuntu:20.04

WORKDIR /app

COPY requirements.txt app.py create_db.py .
COPY templates /app/templates

ENV INSTANA_HOST_ID=123456789
ENV INSTANA_AGENT_KEY=
ENV INSTANA_OTLP_ENDPOINT=127.0.0.1:4317

ENV OTEL_EXPORTER_OTLP_HEADERS=x-instana-key=,x-instana-time=0,x-instana-host=123456789,x-instana-zone=lhb-test-emt

RUN apt update -y; sleep 1; apt install -y gcc unixodbc-dev;   \
    apt install -y python3 python3-pip libsqliteodbc; \
    pip3 install -r requirements.txt;                 \
    python3 create_db.py

CMD ["flask", "run", "--debugger", "--host", "0.0.0.0"]
