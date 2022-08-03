import typing
import pyodbc

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter

# flask
from opentelemetry.instrumentation.flask import FlaskInstrumentor
# odbc with dbapi
from opentelemetry.instrumentation import dbapi

DATABASE_PATH="users.db"

trace.set_tracer_provider(TracerProvider())

trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(ConsoleSpanExporter())
)

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

# trace pyodbc
dbapi.trace_integration(
        connect_module=pyodbc,
        connect_method_name="connect",
        database_system="odbc",
        db_api_integration_factory=DatabaseApiIntegration)


app=Flask(__name__)

# trace flask
FlaskInstrumentor().instrument_app(app)


# APLICACIÓN SIN CAMBIOS, NO SON NECESARIOS EN EL MODO AUTOMATICO
@app.route("/")
@app.route("/index")
def index():
    con = pyodbc.connect("Driver=SQLite3;Database={}".format(DATABASE_PATH))
    cur=con.cursor()
    cur.execute("select * from users")
    data=cur.fetchall()
    return render_template("index.html",datas=data)

@app.route("/add_user",methods=['POST','GET'])
def add_user():
    if request.method=='POST':

        uname   = request.form['uname']
        contact = request.form['contact']

        con = pyodbc.connect("Driver=SQLite3;Database={}".format(DATABASE_PATH))
        cur=con.cursor()
        cur.execute("insert into users(UNAME,CONTACT) values (?,?)",(uname,contact))
        con.commit()

        flash('User Added','success')
        return redirect(url_for("index"))
    return render_template("add_user.html")

@app.route("/edit_user/<string:uid>",methods=['POST','GET'])
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

@app.route("/delete_user/<string:uid>",methods=['GET'])
def delete_user(uid):
    con = pyodbc.connect("Driver=SQLite3;Database={}".format(DATABASE_PATH))
    cur=con.cursor()
    cur.execute("delete from users where UID=?",(uid,))
    con.commit()

    flash('User Deleted','warning')
    return redirect(url_for("index"))

if __name__=='__main__':
    app.secret_key='secret'
    app.run(port=5000, debug=True)
