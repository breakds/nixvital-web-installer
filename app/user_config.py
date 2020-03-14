# This library help persist a global state of user configurations with
# the help of sqlite.

import sqlite3
import pathlib

from flask import g


DB_PATH = pathlib.Path('/tmp/nixvital_installer.db')


def DB():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('/tmp/nixvital_installer.db')
    return db


def FetchUserConfig(db):
    result = {}
    for item in db.cursor().execute('SELECT * FROM UserConfig'):
        result[item[1]] = item[2]
    return result


def SetUserConfig(db, key, value):
    '''Please remember to call commit() after calling this.
    '''
    db.cursor().execute('DELETE FROM UserConfig WHERE VarName = "{}"'.format(key))
    db.cursor().execute('REPLACE INTO UserConfig (VarName, VarVal) VALUES("{}", "{}")'.format(
        key, value))


def InitDB(app, default_nixvital_url):
    if not DB_PATH.exists():
        # Need to `with` this context since this is not a request
        # handler, so that we need this to access `g` in DB()
        with app.app_context():
            db = DB()
            # This creates the table `UserConfig` in the database.
            with app.open_resource('schema.sql', mode='r') as f:
                db.cursor().executescript(f.read())
            SetUserConfig(db, 'nixvital_repo', default_nixvital_url)
            db.commit()
