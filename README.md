#### DEMO MOD
- https://www.vrsofttech.com/python-flask/flask-with-sqlite-crud-application

#### Doc General
- https://opentelemetry.io/docs/concepts/what-is-opentelemetry/
- https://opentelemetry.io/docs/concepts/sdk-configuration/general-sdk-configuration/
- https://www.aspecto.io/blog/getting-started-with-opentelemetry-python/
- https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/dbapi/dbapi.html

#### Automatico
- https://opentelemetry.io/docs/instrumentation/python/automatic/
- https://github.com/open-telemetry/opentelemetry-python-contrib/tree/main/instrumentation
- https://github.com/open-telemetry/opentelemetry-python-contrib/tree/main/instrumentation/opentelemetry-instrumentation-flask
- https://github.com/open-telemetry/opentelemetry-python-contrib/tree/main/instrumentation/opentelemetry-instrumentation-dbapi


~~~text
In order to make a system observable, it must be instrumented. That is,
the code must emit traces, metrics, and logs. The instrumented data must
then be sent to an Observability back-end. There are a number of
Observability back-ends out there, ranging from self-hosted open-source
tools (e.g. Jaeger and Zipkin), to commercial SAAS offerings.
~~~

#### Install

###### DOCKER

~~~bash
$ podman build -t demo-opentelemetry .
$ podman run --rm -it -p 5000:5000 demo-opentelemetry
~~~

###### DEBIAN (solo para sqlite)
~~~bash
$ sudo apt install unixodbc-dev libsqliteodbc
~~~

###### CENTOS (solo para sqlite)
~~~bash
$ sudo dnf install sqliteodbc
~~~

###### PYTHON
~~~bash
$ python -m venv env
$ source env/bin/activate        # (optional)
$
$ pip install opentelemetry-distro
$ pip install opentelemetry-instrumentation-flask
$ pip install opentelemetry-instrumentation-dbapi
$ pip install pyodbc
$ pip install flask
$ pip install requests
~~~

#### RUN SERVER
~~~bash
$ source env/bin/activate         # (optional)
$
$ python app.py
~~~
