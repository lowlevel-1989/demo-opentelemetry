import instana
import typing
import pyodbc

from pymongo import MongoClient

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# flask
from opentelemetry.instrumentation.flask import FlaskInstrumentor
# odbc with dbapi
from opentelemetry.instrumentation import dbapi
# Pymongo instrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor


DATABASE_PATH = "users.db"
MONGO_DATABASE_HOST = "mongodb://some-mongo"
MONGO_DATABASE = "users_count"
MONGO_COLLECTION = "users"

trace.set_tracer_provider(TracerProvider(
    resource=Resource.create({
        ResourceAttributes.SERVICE_NAME: 'otel-demo-opentelemetry',
    })
))

# console mode
trace.get_tracer_provider().add_span_processor(
   BatchSpanProcessor(ConsoleSpanExporter())
)

# trace.get_tracer_provider().add_span_processor(
#         BatchSpanProcessor(OTLPSpanExporter(endpoint="127.0.0.1:4317",
#             insecure=True, timeout=5))
# )

# only for instrumented manually (not used in this project)
tracer = trace.get_tracer_provider().get_tracer(__name__)

# FIX: patch pyodbc error trace
def get_traced_connection_proxy(
    connection, db_api_integration, *args, **kwargs
):
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


PymongoInstrumentor().instrument()


# trace pyodbc
dbapi.trace_integration(
        connect_module=pyodbc,
        connect_method_name="connect",
        database_system="odbc",
        db_api_integration_factory=DatabaseApiIntegration)


app=Flask(__name__)
app.secret_key='secret'

# trace flask
FlaskInstrumentor().instrument_app(app)


def get_user_counter(add=False, delete=False):
    mongo_client = MongoClient(MONGO_DATABASE_HOST)
    mongo_db = mongo_client[MONGO_DATABASE]
    collection = mongo_db[MONGO_COLLECTION]
    users = collection.find_one()
    counter = users["counter"]

    if add:
        new_counter = counter + 1
        collection.update_one(
            {"counter": counter},
            {"$set": { "counter": new_counter }},
        )

    if delete:
        new_counter = counter - 1
        collection.update_one(
            {"counter": counter},
            {"$set": { "counter": new_counter }},
        )

    return counter


# APLICACIÓN SIN CAMBIOS, NO SON NECESARIOS EN EL MODO AUTOMATICO
@app.route("/")
@app.route("/index")
def index():
    con = pyodbc.connect("Driver=SQLite3;Database={}".format(DATABASE_PATH))
    cur=con.cursor()
    cur.execute("select * from users")
    data=cur.fetchall()

    user_counter = get_user_counter()

    return render_template("index.html",datas=data, counter=user_counter)

@app.route("/add_user", methods=['POST','GET'])
def add_user():
    if request.method=='POST':

        uname   = request.form['uname']
        contact = request.form['contact']

        con = pyodbc.connect("Driver=SQLite3;Database={}".format(DATABASE_PATH))
        cur=con.cursor()
        cur.execute("insert into users(UNAME,CONTACT) values (?,?)",(uname,contact))
        con.commit()

        # Increase MongoDB counter
        get_user_counter(add=True)

        flash('User Added','success')
        return redirect(url_for("index"))
    return render_template("add_user.html")

@app.route("/edit_user/<string:uid>", methods=['POST','GET'])
def edit_user(uid):
    con = pyodbc.connect("Driver=SQLite3;Database={}".format(DATABASE_PATH))
    cur=con.cursor()

    if request.method=='POST':

        uname   = request.form['uname']
        contact = request.form['contact']

        cur.execute("update users set UNAME=?,CONTACT=? where UID=?",(uname,contact,uid))
        con.commit()

        flash('User Updated','success')
        return redirect(url_for("index"))

    cur.execute("select * from users where UID=?",(uid,))
    data=cur.fetchone()

    return render_template("edit_user.html",datas=data)

@app.route("/delete_user/<string:uid>", methods=['GET'])
def delete_user(uid):
    con = pyodbc.connect("Driver=SQLite3;Database={}".format(DATABASE_PATH))
    cur=con.cursor()
    cur.execute("delete from users where UID=?",(uid,))
    con.commit()

    # Decrease MongoDB counter
    get_user_counter(delete=True)

    flash('User Deleted','warning')
    return redirect(url_for("index"))

@app.route('/health-check', methods=['GET'])
def health():
    tracer = trace.get_tracer(__name__)
    span = trace.get_current_span()
    span.set_attribute('http.request.header.x_instana_synthetic', '1')
    return 'OK'

if __name__=='__main__':
    app.run(port=5000, debug=True)
