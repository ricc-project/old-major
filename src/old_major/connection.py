import websocket
import requests
import json
import inotify.adapters
import threading
import os
import numpy as np
import asyncio

from time import sleep
from getmac import get_mac_address

# from .led_debugger import LedDebugger
from .parser import parse

# DEBUG = LedDebugger()
ACTUATOR_FILE = '/home/pi/ricc/actuator'

ACTUATOR_ON = False

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
        global ACTUATOR_ON
        # send message to mesh network
        self.actuator_on = not self.actuator_on
        with open(ACTUATOR_FILE, 'w') as actuator_file:
            if self.actuator_on:
                actuator_file.write('1')
                ACTUATOR_ON = True
            else:
                ACTUATOR_ON = False
                actuator_file.write('0')

    def _on_open(self):
        print('Connected')
        # DEBUG.success()

    def _on_message(self, message):
        print('Switching actuator')
        # DEBUG.neutral()
        sleep(1)
        self._switch_actuator()
        self.socket.send(self.SWITCH_SUCCESS)
        # DEBUG.success()

    def _on_error(self, error):
        print('Error "' + error + '"')
        # DEBUG.failed()
        sleep(5)
        print('Retrying')
        self.start_connection()

    def _on_close(self):
        print("Connection lost")
        # DEBUG.failed()
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


def monitor(directory, url, mac_addr):
    token_thread = threading.Thread(target=get_token, args=(url, mac_addr))
    watch_data_thread = threading.Thread(target=watch_for_collects, args=(directory, mac_addr))    
    watch_register_thread = threading.Thread(target=watch_for_register, args=('/home/pi/ricc/dev', mac_addr)) 
    
    watch_data_thread.start()
    watch_register_thread.start()
    token_thread.start()


"""
Watch for new collects and send to the API.
"""
def watch_for_collects(directory: str, mac_addr: str):
    Etc = 0
    Pluv = 0
    # global ACTUATOR_ON/ 
    url = 'http://snowball.lappis.rocks/send_data/'
    irrigation_url = 'http://snowball.lappis.rocks/irrigation/'

    token_file = open('/home/pi/ricc/token', 'r')
    token = token_file.readline()
    token_file.close()

    i = inotify.adapters.Inotify()
    i.add_watch(directory)

    for event in i.event_gen():
        if event:
            event_type = event[1]
            if event_type[0] == 'IN_CLOSE_WRITE':
                fpath = event[2]
                fname = event[3]
                full_path = (fpath + '/' + fname)
                collect_data = parse(full_path)
                if os.path.getsize(full_path):
                    station_id, timestamp = fname[:-4].split('_')
                    headers = {"content-type": "application/json"}
                    partial_msg = {
                        'data': collect_data,
                        'auth_token': token,
                        'central': mac_addr,
                        'name': station_id,
                        'timestamp': timestamp
                    }

                    msg = json.dumps(partial_msg)
                    r = requests.post(url, data=msg, headers=headers, timeout=20)

                    if(r.status_code == 200 or r.status_code == 201):
                        print('Data was sended successfully!\n')
                        os.remove(full_path)
                        # DEBUG.neutral()
                        sleep(1)
                        # DEBUG.success()
                    else:
                        print('error sendind ' + str(r.status_code))
                    
                    # actuator node
                    if station_id == '3' or station_id == '2':
                        soil_moisture = float(collect_data['soil']['moisture1'])

                        air_temperature = float(collect_data['air']['temperature'])
                        air_preessure = float(collect_data['air']['pressure'])
                        air_humidity = float(collect_data['air']['humidity'])
                        wind_speed = float(collect_data['wind']['speed'])
                        solar_rad = float(collect_data['solar']['radiation'])
                        rain_fall = float(collect_data['rain']['rainfall'])
                        
                        Etc += evapotranspiration(air_temperature, air_preessure, air_humidity, wind_speed, solar_rad)
                        print('ETC ' + str(Etc))
                        
                        Pluv += rain_fall
                        print('PLUV ' + str(Pluv))

                        creds = json.dumps({'auth_token': token, 'central': mac_addr})
                        response = requests.post(irrigation_url, data=creds, timeout=20)
                        response_json = json.loads(response.text)
                        can_irrigate = True if response_json['auto_irrigation'] == 'True' else False

                        print('Automatic irrigation is not enabled') if not can_irrigate else ...

                        if soil_moisture < 50 and can_irrigate:
                            print('ETC ' + str(Etc))
                            I = Etc - Pluv
                            Q = 4000 / 3600.0
                            dt = I / Q

                            uptime = dt
                            print('UPTIME ' + str(uptime))
                            turn_on_actuator(uptime)
                            # with open(ACTUATOR_FILE, 'wr') as actuator_file:
                            #     actuator_file.readline()
                            #     print('Turning on actuator')
                            #     actuator_file.write('1')
                            #     sleep(uptime)
                            #     actuator_file.write('0')
                            #     print('Turning off actuator')

                            Etc = 0
                            Pluv = 0


async def turn_on_actuator(uptime):
    global ACTUATOR_ON
    if not ACTUATOR_ON:
        ACTUATOR_ON = True
        with open(ACTUATOR_FILE, 'wr') as actuator_file:
            print('Turning on actuator')
            actuator_file.write('1')
            await asyncio.sleep(uptime)
            actuator_file.write('0')
            print('Turning off actuator')


"""
Try to send a msg with sensor data 5 times.
"""
def resend_data(url, msg, headers):
    for i in range(10):
        print('Resending data\n')
        try:
            r = requests.post(url, data=msg, headers=headers, timeout=20)
            if(r.status_code == 200 or r.status_code == 201):
                break
            sleep(1800)
        except requests.exceptions.RequestException as e:
            sleep(1800)


"""
Constantly makes get requests to get token
"""
def get_token(url: str, mac_addr: str):
    formated_mac = mac_addr.replace(':', '-')
    payload = {'mac': formated_mac}
    while True:
        try:
            response = requests.get(url, params=payload, timeout=20)
            while response.status_code != 200:
                print('Trying to acquire token')
                sleep(10)
                response = requests.get(url, params=payload, timeout=20)
    
            sleep(1)
            f = open('/home/pi/ricc/token', 'w')
            json_data = json.loads(response.text)
            f.write(json_data['auth_token'])
            f.close()
            break
        except requests.exceptions.RequestException as e:
            print('Failed to get token, device without internet conection, retraying!\n')
            sleep(30)


"""
Let the server know the central is online
"""
def signup(url: str, mac_addr: str):
    headers = {"content-type": "application/json"}
    msg = json.dumps({'mac_address': mac_addr})
    
    while True:
        try:
            response = requests.post(url, data=msg, headers=headers, timeout=20)
            if response.status_code == 201:
                sleep(1)

            return response
        except requests.exceptions.RequestException as e:
            print('Failed to signup, device without internet conection, retraying!\n')
            sleep(30)


def watch_for_register(directory: str, mac_addr: str):
    create_station_url = 'http://snowball.lappis.rocks/create_station/'
    create_actuator_url = 'http://snowball.lappis.rocks/create_actuator/'
    status_url = 'http://snowball.lappis.rocks/node_status/'
    
    headers = {"content-type": "application/json"}

    previous_devices = []
    while True:
        sleep(0.5)
        devices = os.listdir(directory)
        for d in previous_devices:
            if d not in devices:
                station_name = d.split('_')[1]
                msg = json.dumps(
                    {
                        'auth_token': auth_token(),
                        'central': mac_addr,
                        'name': station_name
                    }
                )
                response = requests.post(status_url, data=msg, headers=headers, timeout=20)
                if response.status_code == 200:
                    print('Station ' + station_name + ' has leaved the mesh network')

        previous_devices = devices
        for d in devices:
            if d not in previous_devices:
                station_name = d.split('_')[1]
                msg = json.dumps(
                    {
                        'auth_token': auth_token(),
                        'central': mac_addr,
                        'name': station_name
                    }
                )
                # actuator node
                if station_name == '1':
                    response = requests.post(create_actuator_url, data=msg, headers=headers, timeout=20)
                else:
                    response = requests.post(create_station_url, data=msg, headers=headers, timeout=20)

                if response.status_code == 201:
                    print('Station registered ' + station_name)
                else:
                    print('Station ' + station_name + ' already registered')
                    requests.post(status_url, data=msg, headers=headers, timeout=20)
                    print('Station ' + station_name + ' entered in the network')

        previous_devices = devices


def auth_token():
    with open('/home/pi/ricc/token', 'r') as f:
        return f.readline()


def evapotranspiration(air_temperature, air_pressure, air_humidity, wind_speed, solar_rad):
    T = air_temperature
    P = air_pressure / 10.0
    UR = air_humidity
    uz = wind_speed
    Rn = solar_rad * 1e-3

    x = 0
    G = 0
    A = 80e-5
    z = 1.53

    gamma = A*P

    Delta = 4098*(0.6108*np.e**(17.27*T/(T+237.3))) / ((T + 237.3)**2)

    es = 0.61121*np.e**((18.678 - T/234.84) * (T/(257.14 + T)))

    ea = UR*es / 100.0

    u2 = uz*(4.87/np.log(67.8*z - 5.42))

    Eto = (0.408*Delta*(Rn - G) + gamma*(900/(T + 273))*u2*(es - ea)) / (Delta + (1 + 0.34*u2))

    Kc = -0.00022*x**2 + 0.0318*x + 0.4588

    return Kc * Eto


# def evapotranspiration():
#     T = collect_data['air']['temperature']
#     P = collect_data['air']['pressure'] / 10.0
#     UR = collect_data['air']['humidity']
#     uz = collect_data['wind']['speed']
#     Rn = collect_data['solar']['radiation'] * 1e-3
    
    #acumulativo
    #Pluv += collect_data['rain']['rainfall']

    # x = 0
    # G = 0
    # A = 80e-5
    # z = 1.53

    # gamma = A*P

    # Delta = 4098*(0.6108*np.e**(17.27*T/(T+237.3))) / ((T + 237.3)**2)

    # es = 0.61121*np.e**((18.678 - T/234.84) * (T/(257.14 + T)))

    # ea = UR*es / 100.0

    # u2 = uz*(4.87/np.log(67.8*z - 5.42))

    # Eto = (0.408*Delta*(Rn - G) + gamma*(900/(T + 273))*u2*(es - ea)) / (Delta + (1 + 0.34*u2))

    # Kc = -0.00022*x**2 + 0.0318*x + 0.4588

    # acumalitvo
    # tem que zerar quando ligar
    # Etc += Kc * Eto

    # I = Etc - Pluv

    # Q = 4000 / 3600.0

    # dt = I / Q
