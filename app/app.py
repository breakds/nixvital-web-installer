#! /usr/bin/env python3

import os
import sqlite3

from flask import g, Flask, redirect, render_template, request

from user_config import InitDB, DB, FetchUserConfig, SetUserConfig

app = Flask(__name__)

@app.teardown_appcontext
def Close(exception):
    DB().close()


@app.route('/')
def home():
    cfg = FetchUserConfig(DB())
    return render_template("index.html", text=cfg['text'])


@app.route('/change')
def change():
    db = DB()
    SetUserConfig(db, 'text', 'changed!')
    db.commit()
    return redirect('/')


if __name__ == '__main__':
    InitDB(app)
    app.run()
