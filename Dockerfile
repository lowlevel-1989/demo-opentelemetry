FROM ubuntu:20.04

WORKDIR /app

COPY requirements.txt app.py create_db.py .
COPY templates /app/templates

RUN apt update -y; apt install -y gcc unixodbc-dev;   \
    apt install -y python3 python3-pip libsqliteodbc; \
    pip3 install -r requirements.txt;                 \
    python3 create_db.py

CMD ["flask", "run", "--debugger", "--host", "0.0.0.0"]
