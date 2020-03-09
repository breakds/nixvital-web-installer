#! /usr/bin/env python3

import os
import sqlite3

from flask import g, Flask, redirect, render_template, request, url_for, session

from user_config import InitDB, DB, FetchUserConfig, SetUserConfig
import partutils
import vitalutils

app = Flask(__name__)
app.secret_key = b'\xb7\x0b\x86\xc0+\x1a&\xd6 \xdfx\\\x90O\xac\xae'


@app.teardown_appcontext
def Close(exception):
    DB().close()


class BasicInfo(object):
    def __init__(self, cfg):
        self.username = cfg.get('username', '')
        self.hostname = cfg.get('hostname', '')


def MakeDisplayMessage(text='', accent='positive'):
    return {
        'text': text,
        'accent': accent,
        'visible': 'visible' if text != '' else 'hidden',
    }


def ExtractMessage(session, key):
    if key in session:
        msg = session[key]
        session.pop(key, None)
        return msg
    return MakeDisplayMessage()


def GetMountTable(cfg):
    mount_table = {}
    for loc in partutils.MOUNT_LOCATIONS:
        mount_table[loc] = cfg.get(loc, None)
    return mount_table


def GetVitalInfo(cfg):
    return {
        'repo': cfg.get('nixvital_repo', vitalutils.DEFAULT_REPO),
    }


@app.route('/', methods=['GET', 'POST'])
def home():
    cfg = FetchUserConfig(DB())
    return render_template("index.html",
                           basic_info=BasicInfo(cfg),
                           basic_info_message=ExtractMessage(session, 'basic_info_message'),
                           mount_table=GetMountTable(cfg),
                           mount_table_message=ExtractMessage(session, 'mount_table_message'),
                           partition_info=partutils.GetBlockInfo(
                               session.get('active_device', None)),
                           vital_info=GetVitalInfo(cfg))


# TODO(breakds): Add logging.
@app.route('/basic_info', methods=['GET', 'POST'])
def update_basic_info():
    db = DB()
    # TODO(breakds): Save only if valid.
    SetUserConfig(db, 'username', request.form.get('username', ''))
    SetUserConfig(db, 'hostname', request.form.get('hostname', ''))
    session['basic_info_message'] = MakeDisplayMessage(
        'Successfully updated basic info.')
    db.commit()

    return redirect(url_for('home'))


@app.route('/select_device', methods=['GET', 'POST'])
def select_device():
    session['active_device'] = request.args.get('name', None)
    return redirect(url_for('home'))


@app.route('/propose_mount_table', methods=['GET', 'POST'])
def propose_mount_table():
    db = DB()
    for loc in partutils.MOUNT_LOCATIONS:
        SetUserConfig(db, loc, request.form.get(loc, None))
    db.commit()
    session['mount_table_message'] = MakeDisplayMessage(
        'Updated mount table successfully.')
    return redirect(url_for('home'))


if __name__ == '__main__':
    InitDB(app)
    app.run()
