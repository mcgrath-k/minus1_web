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

last_pop = '7,420,420,420'
last_presses = [
    'button 0 pressed at (39.6860332, -104.9379315) at 2019-01-15 05:13:30.164099 - population 7,677,252,971'
]

script_path = os.path.dirname(os.path.abspath(__file__))


conn = sqlite3.connect(os.path.join(fullPath, 'press_history.db'))
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS presses (button_num, coordinates, thedate, population)''')
press_sql = "INSERT INTO presses (button_num, coordinates, thedate , population) VALUES (?, ?, ?, ?);"


app = Flask(__name__)
app.config['SECRET_KEY'] = 'jriojfiofjoisj'  # TODO literally anything else
socketio = SocketIO(app)


@app.route('/')
def hello_world():
    return render_template('index.html', key=random.random(), pop=last_pop, presses=last_presses)


def get_pop():
    global last_pop
    pop = int(requests.get("http://localhost:3000").text) - 1
    pop = '{:,}'.format(pop)
    last_pop = pop
    return pop


@app.route('/press')
def press():
    global last_presses
    button_id = request.args.get('button', '')
    pop = get_pop()
    if button_id:
        coords = BUTTON_COORDS.get(button_id, '(???, ???)')
        message = 'button {} pressed at {} at {} - population {}'.format(button_id, coords,
                                                                         str(datetime.datetime.now()), pop)
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
