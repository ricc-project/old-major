import socket
from time import sleep
from getmac import get_mac_address

def start_connection(host, port):
    current_ip = socket.gethostbyname(socket.gethostname())
    mac_addr = get_mac_address(interface='eth0')

    msg = f'ip - {current_ip}, mac - {mac_addr}'

    send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while send_socket.connect_ex((host, port)) != 0:
        print('Faieled to stabilish connection')
        sleep(10)
        print('Retraying connection')

    send_socket.sendall(bytes(msg, 'raw_unicode_escape'))
    buffer = send_socket.recv(4)
    response = int(buffer)
    print('response ', str(response))
    
    while response != 200:
        send_socket.sendall(bytes(msg, 'raw_unicode_escape'))
        buffer = send_socket.recv(4)
        response = int(buffer.decode('utf-8'))
    
    while True:
        buffers = send_socket.recv(1024)
        turn_on = bool(buffer)


def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()
    print('Server listening')
    while True:
        conn, addr = server_socket.accept()
        print(f'Connected with {addr}')
        while True:
            buffer = conn.recv(1024)
            if not buffer:
                break
            msg = str(buffer)
            print(f'Received {msg} from {addr}')
            conn.sendall(str.encode(str(200)))
    