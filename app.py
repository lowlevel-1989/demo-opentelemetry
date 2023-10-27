import pyodbc

from pymongo import MongoClient

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash


DATABASE_PATH = "users.db"
MONGO_DATABASE_HOST = "mongodb://0.0.0.0"
MONGO_DATABASE = "users_count"
MONGO_COLLECTION = "users"


app=Flask(__name__)
app.secret_key='secret'


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

    print('VINICIO')

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
