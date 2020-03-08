#! /usr/bin/env python3

import os
import sqlite3

from flask import g, Flask, redirect, render_template, request, url_for, session

from user_config import InitDB, DB, FetchUserConfig, SetUserConfig

app = Flask(__name__)
app.secret_key = b'\xb7\x0b\x86\xc0+\x1a&\xd6 \xdfx\\\x90O\xac\xae'


@app.teardown_appcontext
def Close(exception):
    DB().close()


@app.route('/', methods=['GET', 'POST'])
def home():
    cfg = FetchUserConfig(DB())
    username = cfg.get('username', '')
    hostname = cfg.get('hostname', '')

    basic_info_message = ''
    if 'basic_info_message' in session:
        basic_info_message = session['basic_info_message']
        session.pop('basic_info_message', None)

    basic_info_message_visible = 'visible' if basic_info_message != '' else 'hidden'
    
    return render_template("index.html",
                           username=username,
                           hostname=hostname,
                           basic_info_message=basic_info_message,
                           basic_info_message_visible=basic_info_message_visible)


# TODO(breakds): Add logging.
@app.route('/basic_info', methods=['GET', 'POST'])
def update_basic_info():
    db = DB()
    # TODO(breakds): Save only if valid.
    SetUserConfig(db, 'username', request.form.get('username', ''))
    SetUserConfig(db, 'hostname', request.form.get('hostname', ''))
    session['basic_info_message'] = 'Successfully updated basic info.'
    db.commit()

    return redirect(url_for('home'))


if __name__ == '__main__':
    InitDB(app)
    app.run()
