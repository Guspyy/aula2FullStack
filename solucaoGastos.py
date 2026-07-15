import sqlite3

def get_Connection():
    conn = sqlite3.connect("gastos.db")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn
print(get_Connection())