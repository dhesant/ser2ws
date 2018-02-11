#!/usr/bin/python3
import sys
import ssl
import signal
import traceback
import argparse
from SimpleWebSocketServer import SimpleWebSocketServer, SimpleSSLWebSocketServer, WebSocket
import serial
import serial.threaded

wsConnections = []
serialTransports = []
device = ""

class SimpleServer(WebSocket):
    def handleMessage(self):
        print("WebSocket:", self.address, self.data)
        for con in wsConnections:
            con.sendMessage("$" + self.data)
        for transport in serialTransports:
            transport.write_line(self.data)

    def handleConnected(self):
        print("WebSocket:", self.address, "Connected")
        wsConnections.append(self)

    def handleClose(self):
        wsConnections.remove(self)
        print("WebSocket:", self.address, "Closed")
        
class SimpleSerial(serial.threaded.LineReader):
    def connection_made(self, transport):
        super(SimpleSerial, self).connection_made(transport)
        serialTransports.append(self)
        print("Connected to", device)

    def handle_line(self, data):
        print("Serial:", data)
        for con in wsConnections:
            con.sendMessage(data)

    def connection_lost(self, exc):
        serialTransports.remove(self)
        print("Closed Port")
        if exc:
            traceback.print_exc(exc)
            sys.exit(1)
        sys.exit(0)

if __name__ == "__main__":
    # Test python version
    if sys.version_info < (3, 4):
        print("Wrong python version, required is at least 3.4")
        exit(1)
        # Test PySerial Version
    pyserial_version = [int(i) for i in serial.__version__.split('.')]
    if pyserial_version[0] < 3:
        print("Wrong pyserial version, required is at least 3.0")
        exit(1)

    parser = argparse.ArgumentParser(description="ser2ws v1.0.0")
    parser.add_argument(
        '-V', '--version', action='version', version="ser2ws v1.0.0")
    parser.add_argument(
        '-v', '--verbose', action='count', default=0,
        help="Enable verbose output")
    parser.add_argument(
        '-l', '--listen', default=':8989',
        help="Listen URL (default: :8989)")
    parser.add_argument(
        'port',
        help="Serial port (example: /dev/ttyUSB0)")
    parser.add_argument(
        'baud', type=int,
        help="Serial baud rate (example: 115200)")
    # parser.add_argument(
    #     '--parity', nargs='?', default='NONE', choices=['NONE', 'EVEN', 'ODD'],
    #     help="Serial parity")
    # parser.add_argument(
    #     '--stopbits', nargs='?', type=int, default=1, choices=[1, 2],
    #     help="Serial  stop bits")
    parser.add_argument(
        '--ssl', action='store_true',
        help="Enable SSL")
    parser.add_argument(
        '--cert', nargs=1, 
        help="SSL Certificate (example: ./cert.pem)")
    parser.add_argument(
        '--key', nargs=1, 
        help="SSL Key File (example: ./key.pem)")
    parser.add_argument(
        '--sslver', type=int, default=ssl.PROTOCOL_TLSv1_2,
        help="SSL Protocol Version (example: 5)")
    args = parser.parse_args()

    address, port = args.listen.split(':')
    if not address:
        address = ''
    port = int(port) if port else 8989
    
    print("Starting server at " + address + ":" + str(port))
    if(args.ssl):
        print("SSL Enabled")
    
    if args.ssl:
        server = SimpleSSLWebSocketServer(address, port, SimpleServer, args.cert, args.key, version=args.sslver)
    else:
        server = SimpleWebSocketServer(address, port, SimpleServer)

    ser = serial.Serial(args.port, baudrate = args.baud, timeout=1)
    device = ser.name
    serial = serial.threaded.ReaderThread(ser, SimpleSerial)
    serial.start()
    
    def close_sig_handler(signal, frame):
        serial.close()
        server.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, close_sig_handler)
    server.serveforever()
