#!/usr/bin/env python3

import socket

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65432        # The port used by the server

current_ip = socket.gethostbyname(socket.gethostname())

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket:
    socket.connect((HOST, PORT))
    socket.sendall(bytes(current_ip, 'raw_unicode_escape'))
    data = socket.recv(1024)

print('Received', repr(data))