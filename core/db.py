import os
import sqlite3


def get_db_connection(persist_dir, conn, name=''):
    "returns an sqlite3 connection to a persistent database"

    if not name:
        name = '%s.%s.db' % (conn.nick, conn.server)

    filename = os.path.join(persist_dir, name)

    return sqlite3.connect(filename, timeout=10)