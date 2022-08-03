import sqlite3 as sql

if __name__ == "__main__":

    #connect to SQLite
    con = sql.connect('users.db')

    #Create a Connection
    cur = con.cursor()

    #Drop users table if already exsist.
    cur.execute("DROP TABLE IF EXISTS users")

    #Create users table  in db_web database
    sql ='''CREATE TABLE "users" (
        "UID"	INTEGER PRIMARY KEY AUTOINCREMENT,
        "UNAME"	TEXT,
        "CONTACT"	TEXT
    )'''
    cur.execute(sql)

    #commit changes
    con.commit()

    #close the connection
    con.close()
