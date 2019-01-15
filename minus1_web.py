# melody horn
import random
import datetime

from flask import Flask, render_template, request
from flask_socketio import SocketIO
import requests


BUTTON_COORDS = {
    '0': '(39.6860332, -104.9379315)',
}


last_pop = '7,420,420,420'
last_presses = [
    'button pressed at (39.6860332, -104.9379315) at 2019-01-15 05:13:30.164099 - population 7,677,252,971'
]


app = Flask(__name__)
app.config['SECRET_KEY'] = 'jriojfiofjoisj' # TODO literally anything else
socketio = SocketIO(app)


@app.route('/')
def hello_world():
    return render_template('index.html', key=random.random(), pop=last_pop, presses=last_presses)


def get_pop():
    global last_pop
    pop = int(requests.get("http://192.168.137.253:3000").text) - 1
    pop = '{:,}'.format(pop)
    last_pop = pop
    return pop


@app.route('/press')
def press():
    global last_presses
    button_id = request.args.get('button', '')
    coords = BUTTON_COORDS.get(button_id, '(???, ???)')
    pop = get_pop()
    message = 'button pressed at {} at {} - population {}'.format(coords, str(datetime.datetime.now()), pop)
    last_presses = last_presses + [message]
    socketio.emit('press', message)
    return pop.replace(',', '')


@socketio.on('ping')
def client_ping(_):
    print('Got ping')
    pop = get_pop()
    socketio.emit('pop', pop)
    return "beans"


if __name__ == '__main__':
    socketio.run(app)
