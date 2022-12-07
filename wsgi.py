#gunicorn -c gunicorn.conf.py wsgi:app

#Instana
import instana
import typing
import pyodbc

from app import app
from werkzeug.middleware.proxy_fix import ProxyFix

# flask
from opentelemetry.instrumentation.flask import FlaskInstrumentor
# odbc with dbapi
from opentelemetry.instrumentation import dbapi
# Pymongo instrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor

def get_traced_connection_proxy(connection, db_api_integration, *args, **kwargs):
    class TracedConnectionProxy:
        def __init__(self, connection):
            self._connection = connection

        def __getattr__(self, name):
            return object.__getattribute__(
                object.__getattribute__(self, "_connection"), name
            )

        def cursor(self, *args, **kwargs):
            return dbapi.get_traced_cursor_proxy(
                self._connection.cursor(*args, **kwargs), db_api_integration
            )

        # For some reason this is necessary as trying to access the close
        # method of self._connection via __getattr__ leads to unexplained
        # errors.
        def close(self):
            self._connection.close()

    return TracedConnectionProxy(connection)

class DatabaseApiIntegration(dbapi.DatabaseApiIntegration):
    def wrapped_connection(
            self,
            connect_method: typing.Callable[..., typing.Any],
            args: typing.Tuple[typing.Any, typing.Any],
            kwargs: typing.Dict[typing.Any, typing.Any],
    ):
        """Add object proxy to connection object."""
        connection = connect_method(*args, **kwargs)
        self.get_connection_attributes(connection)
        return get_traced_connection_proxy(connection, self)

# trace mongodb
PymongoInstrumentor().instrument()

# trace pyodbc
dbapi.trace_integration(
    connect_module=pyodbc,
    connect_method_name="connect",
    database_system="odbc",
    db_api_integration_factory=DatabaseApiIntegration)



app.wsgi_app = ProxyFix(app.wsgi_app)

# trace flask
FlaskInstrumentor().instrument_app(app)
