# melody horn
import random
import datetime
import sqlite3
import os

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import requests

BUTTON_COORDS = {
    '0': '(39.7614419, -104.9846901)',
}

fullPath = os.path.dirname(os.path.abspath(__file__))


conn = sqlite3.connect(os.path.join(fullPath, 'press_history.db'))
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS presses (button_num, coordinates, thedate, population)''')
c.execute('CREATE TABLE IF NOT EXISTS globals (name PRIMARY KEY, value)')
press_sql = "INSERT INTO presses (button_num, coordinates, thedate , population) VALUES (?, ?, ?, ?);"


def get_global(name, default=None):
    c.execute('SELECT name, value FROM globals WHERE name = ?', (name,))
    result = c.fetchone()
    if result is None:
        return default
    else:
        return result[1]


def set_global(name, value):
    c.execute('INSERT OR REPLACE INTO globals (name, value) VALUES (?, ?)', (name, value))
    conn.commit()


def format_press_msg(button, coords, timestamp, pop):
    return 'button {} pressed at {} at {} - population {}'.format(button, coords, timestamp, pop)


def get_pop():
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    today = datetime.datetime(now.year, now.month, now.day, tzinfo=datetime.timezone.utc)
    jul18 = datetime.datetime(2018, 7, 1, tzinfo=datetime.timezone.utc)
    seconds_today = (now - today).total_seconds()
    seconds_since_jul18 = round((now - jul18).total_seconds())

    pop = round(seconds_since_jul18 * 2.5907 + 7632819325 - seconds_today * 2.5907) + round(
        seconds_today * 4.4634) - round(seconds_today * 1.8727)

    pop = pop - 1
    pop = '{:,}'.format(pop)
    set_global('last_pop', pop)
    return pop


c.execute("SELECT button_num, coordinates, thedate, population FROM presses ORDER BY thedate DESC LIMIT 30")
last_presses = [format_press_msg(*tuple(x)) for x in reversed(c.fetchall())]


app = Flask(__name__)
socketio = SocketIO(app)


@app.route('/')
def hello_world():
    return render_template('index.html', key=random.random(), pop=get_pop(), presses=last_presses)


@app.route('/checkconnection')
def test():
    return ""


@app.route('/press')
def press():
    global last_presses
    button_id = request.args.get('button', '')
    pop = get_pop()
    if button_id:
        coords = BUTTON_COORDS.get(button_id, '(???, ???)')
        message = format_press_msg(button_id, coords, str(datetime.datetime.now()), pop)
        c.execute(press_sql, (button_id, str(coords), str(datetime.datetime.now()), pop))
        conn.commit()
        last_presses = last_presses + [message]
        socketio.emit('press', message)

    return pop.replace(',', '')


@app.route('/database')
def data_check():
    print(c.fetchall())
    return 0


@socketio.on('sync')
def sync(use_utc):
    if use_utc:
        now = datetime.datetime.now(tz=datetime.timezone.utc)
    else:
        now = datetime.datetime.now()
    emit('sync', now.isoformat(timespec='milliseconds'))


if __name__ == '__main__':
    socketio.run(app)
