#!/usr/bin/env python3

import socket
from getmac import get_mac_address


HOST = 'shelby-571.local'  # The server's hostname or IP address
PORT = 65432        # The port used by the server

current_ip = socket.gethostbyname(socket.gethostname())
mac_addr = get_mac_address(interface='eth0')

print(f'my mc is {mac_addr}')

msg = f'ip - {current_ip}, mac - {mac_addr}'

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket:
    socket.connect((HOST, PORT))
    socket.sendall(bytes(msg, 'raw_unicode_escape'))
    data = socket.recv(1024)

print('Received', repr(data))