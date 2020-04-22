#! /usr/bin/env python3

import os
import sqlite3
import click
import yaml

from flask import current_app, g, Flask, redirect, render_template, request, url_for, session

from .utils.user_config import InitDB, DB, FetchUserConfig, SetUserConfig
from .utils import partutils
from .utils import vitalutils
from .utils import generator

app = Flask(__name__)
app.secret_key = b'\xb7\x0b\x86\xc0+\x1a&\xd6 \xdfx\\\x90O\xac\xae'
app.config['extra_fields'] = []


INSTALL_ROOT = '/mnt'


@app.teardown_appcontext
def Close(exception):
    DB().close()


class BasicInfo(object):
    def __init__(self, cfg):
        self.username = cfg.get('username', '')
        self.hostname = cfg.get('hostname', '')
        self.extra_fields = []
        for field in current_app.config.get('extra_fields', []):
            self.extra_fields.append({
                'key': field['key'],
                'description': field['description'],
                'name': field['name'],
                'value': cfg.get(field['key'], ''),
            })


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


def GetVitalInfo(cfg, session):
    message = session.get('nixvital_repo_message', None)
    session.pop('nixvital_repo_message', None)
    if message is None:
        if vitalutils.HasNixvitalDir('/tmp'):
            message = vitalutils.Message('success')
        else:
            message = vitalutils.Message()
    return {
        'repo': cfg.get('nixvital_repo', vitalutils.DEFAULT_REPO),
        'message': message,
        'can_proceed': vitalutils.HasNixvitalDir('/tmp')
    }


def GetGeneratorInfo(cfg, session):
    message = session.get('generator_message', {
        'visible': 'hidden',
        'accent': 'positive',
    })
    session.pop('generator_message', None)
    return {
        'machine_list': generator.GetMachineList('/tmp/nixvital'),
        'machine': cfg.get('machine', None),
        'message': message,
    }


@app.route('/', methods=['GET', 'POST'])
def home():
    cfg = FetchUserConfig(DB())
    return render_template('index.html',
                           basic_info=BasicInfo(cfg),
                           basic_info_message=ExtractMessage(session, 'basic_info_message'),
                           mount_table=GetMountTable(cfg),
                           mount_table_message=ExtractMessage(session, 'mount_table_message'),
                           partition_info=partutils.GetBlockInfo(
                               session.get('active_device', None)),
                           vital_info=GetVitalInfo(cfg, session),
                           generator_info=GetGeneratorInfo(cfg, session))


# TODO(breakds): Add logging.
@app.route('/basic_info', methods=['GET', 'POST'])
def update_basic_info():
    db = DB()
    # TODO(breakds): Save only if valid.
    SetUserConfig(db, 'username', request.form.get('username', ''))
    SetUserConfig(db, 'hostname', request.form.get('hostname', ''))
    for field in current_app.config.get('extra_fields', []):
        SetUserConfig(db, field['key'], request.form.get(field['key'], ''))
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
    cfg = FetchUserConfig(db)
    if not partutils.ExecutePartition(cfg, INSTALL_ROOT):
        session['mount_table_message'] = MakeDisplayMessage(
            'Update mount table failed.', 'negative')
    else:
        session['mount_table_message'] = MakeDisplayMessage(
            'Updated mount table successfully.')
    return redirect(url_for('home'))


@app.route('/clone_nixvital', methods=['GET', 'POST'])
def clone_nixvital():
    path = vitalutils.CloneNixvital('/tmp', request.form.get('nixvital_url'))
    if path is None:
        session['nixvital_repo_message'] = vitalutils.Message('fail')
        # TODO(breakds): Set error message header
        return redirect(url_for('home'))
    db = DB()
    SetUserConfig(db, 'nixvital_repo', request.form.get('nixvital_url'))
    SetUserConfig(db, 'nixvital_local', path)
    db.commit()
    session['nixvital_repo_message'] = vitalutils.Message('success')
    # TODO(breakds): Set success message.
    return redirect(url_for('home'))


@app.route('/generate', methods=['GET', 'POST'])
def run_generate():
    machine = request.form.get('machine')
    db = DB()
    SetUserConfig(db, 'machine', machine)
    db.commit()
    cfg = FetchUserConfig(db)
    generator.GenerateHardwareConfig(INSTALL_ROOT)
    generator.SetupNixvital(INSTALL_ROOT, '/tmp/nixvital')
    extra_fields_map = []
    for field in current_app.config.get('extra_fields', []):
        extra_fields_map.append({
            'variable': field['key'],
            'value': cfg.get(field['key'], ''),
        })
    generator.RewriteConfiguration(
        INSTALL_ROOT,
        cfg.get('username', None),
        cfg.get('machine', None),
        cfg.get('hostname', None), extra_fields_map)
    session['generator_message'] = generator.Message()
    return redirect(url_for('home'))


# Example extra filed yaml file
#
# - key: "gmail_account"
#   name: "Gmail Account"
#   nix: "vital.gmail_account"
#   description: "Your gmail account e.g. (break.yang)"
# - key: "fullname"
#   name: "Full Name"
#   nix: "vital.weride.gitUserName"
#   description: "Your full name (e.g. Break Yang)"
@click.command()
@click.option('--default_nixvital_url', default='https://github.com/breakds/nixvital.git',
              type=click.STRING, help='The url to the default nixvital repository.')
@click.option('--extra_field_yaml', '-e', default='',
              type=click.Path(), help='The yaml file that contains extra fields to handle.')
def main(default_nixvital_url, extra_field_yaml):
    if extra_field_yaml:
        with open(extra_field_yaml, 'r') as f:
            app.config.update(extra_fields=yaml.load(f, Loader=yaml.Loader))
    InitDB(app, default_nixvital_url)
    app.run()


if __name__ == '__main__':
    main()
