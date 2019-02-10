# melody horn
import random
import datetime
import sqlite3
import os

from flask import Flask, render_template, request
from flask_socketio import SocketIO
import requests

BUTTON_COORDS = {
    '0': '(39.6860332, -104.9379315)',
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


c.execute("SELECT button_num, coordinates, thedate, population FROM presses ORDER BY thedate DESC LIMIT 30")
last_presses = [format_press_msg(*tuple(x)) for x in reversed(c.fetchall())]


app = Flask(__name__)
app.config['SECRET_KEY'] = 'jriojfiofjoisj'  # TODO literally anything else
socketio = SocketIO(app)


@app.route('/')
def hello_world():
    return render_template('index.html', key=random.random(), pop=get_global('last_pop', '7,420,420,420'), presses=last_presses)


def get_pop():
    try:
        pop = int(requests.get("http://localhost:3000").text) - 1
        pop = '{:,}'.format(pop)
        set_global('last_pop', pop)
        return pop
    except requests.exceptions.ConnectionError:
        print('Failed to connect to population server')
        return get_global('last_pop', '7,420,420,420')

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
    else:
        message = 'mobile access'

    conn.commit()
    last_presses = last_presses + [message]
    socketio.emit('press', message)
    return pop.replace(',', '')


@socketio.on('ping')
def client_ping(_):
    print('Got ping')
    pop = get_pop()
    socketio.emit('pop', pop)
    return "beans"


@app.route('/database')
def data_check():
    print(c.fetchall())
    conn.close()
    return 0


if __name__ == '__main__':
    socketio.run(app)
