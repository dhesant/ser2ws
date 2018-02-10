import sys
import ssl
import signal
from optparse import OptionParser
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
import serial

connections = [];
class SimpleServer(WebSocket):
    def handleMessage(self):
        # Serial.write(self.data)
        self.message(self.data)

    def handleConnected(self):
        print(self.address, 'connected')
        connections.append(self)

    def handleClose(self):
        clients.remove(self)
        print(self.address, 'closed')
        
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

    print("Init Complete")
        
    parser = OptionParser(usage="usage: %prog [options]", version="%prog 1.0")
    parser.add_option("--host", default='', type='string', action="store", dest="host", help="hostname (localhost)")
    parser.add_option("--port", default=8989, type='int', action="store", dest="port", help="port (8000)")
    parser.add_option("--ssl", default=0, type='int', action="store", dest="ssl", help="ssl (1: on, 0: off (default))")
    parser.add_option("--cert", default='./cert.pem', type='string', action="store", dest="cert", help="cert (./cert.pem)")
    parser.add_option("--key", default='./key.pem', type='string', action="store", dest="key", help="key (./key.pem)")
    parser.add_option("--ver", default=ssl.PROTOCOL_TLSv1, type=int, action="store", dest="ver", help="ssl version")
    (options, args) = parser.parse_args()

    print("Starting server at " + options.host + ":" + options.port + "with SSL" if (options.ssl == 1) else "")
    
    if options.ssl == 1:
        server = SimpleSSLWebSocketServer(options.host, options.port, SimpleServer, options.cert, options.key, version=options.ver)
    else:
        server = SimpleWebSocketServer(options.host, options.port, SimpleServer)

    def close_sig_handler(signal, frame):
        server.close()
        sys.exit()

    signal.signal(signal.SIGINT, close_sig_handler)
    server.serveforever()
