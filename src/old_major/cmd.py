import argparse
import os

from getmac import get_mac_address

from .connection import WSConnection, watch_for_collects


def main():
    parser = argparse.ArgumentParser()
    
    parser.add_argument('host', type=str, help='a hostname to make http and tcp requests',
                        nargs='?', default='localhost:8000')
    
    parser.add_argument('interface', type=str, help='internet interface used',
                        nargs='?', default='eth0')

    parser.add_argument('directory', type=str, help='directory where sensor data is saved',
                        nargs='?', default='/tmp/ricc/')
    
    args = parser.parse_args()

    mac_addr = get_mac_address(args.interface)
    
    if mac_addr:
        if not os.path.exists(args.directory):
            os.makedirs(args.directory)

        ws_url = f'ws://{args.host}/ws/?mac={mac_addr}'
        print('ws ', ws_url) 
        connection = WSConnection(ws_url, args.interface)
        connection.start_connection()
        watch_for_collects(args.directory)
    else:
        print("Invalid internet interface, couldn't get device mac address")
