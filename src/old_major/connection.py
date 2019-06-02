import websocket
import requests
import json
import inotify.adapters
import threading

from time import sleep
from getmac import get_mac_address


class WSConnection:

    SWITCH_SUCCESS = json.dumps({'message': 200})

    def __init__(self, url, interface="eth0"):
        self.url = url
        self.interface = interface
        self.actuator_on = False
        self.token = None
        self.socket = websocket.WebSocketApp(self.url,
                                            on_open = self._on_open,
                                            on_message = self._on_message,
                                            on_error = self._on_error,
                                            on_close = self._on_close)

        self.socket_thread = threading.Thread(target=self._run_forever)
        self.socket_thread.daemon = True

    def start_connection(self):
        if not self.socket_thread.is_alive():
            self.socket_thread.start()
            
    def _run_forever(self):
        while True:
            sleep(2)
            print('Trying to connect')
            self.socket.run_forever()

    def _switch_actuator(self):
        # send message to mesh network
        self.actuator_on = not self.actuator_on
    
    def _on_open(self):
        print('Connected')

    def _on_message(self, message):
        print('Switching actuator')
        self._switch_actuator()
        self.socket.send(self.SWITCH_SUCCESS)

    def _on_error(self, error):
        print(f'Error "{error}"')
        sleep(5)
        print('Retrying')
        self.start_connection()

    def _on_close(self):
        print("Connection lost")
        sleep(5)
        print('Trying to stabilish connection')
        self.start_connection()


"""
Send data to the API.
"""
def send_http_data(url: str, token: str, data: dict):
    payload = {'Authorization': token}
    msg = json.dumps(data)
    response = requests.post(url, data=payload, json=msg)
    
    return response.status


"""
Watch for new collects and send to the API.
"""
def watch_for_collects(directory: str):
    i = inotify.adapters.Inotify()

    i.add_watch(directory)

    for event in i.event_gen():
        if event:
            event_type = event[1]
            if event_type[0] == 'IN_CLOSE_WRITE':
                print('path ' + event[2])
                print('name ' + event[3])
