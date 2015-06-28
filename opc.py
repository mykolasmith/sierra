import socket

class Host(object):
    
    def __init__(self, server_ip_port):
        self._ip, self._port = server_ip_port.split(':')
        self._port = int(self._port)
        
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self._ip, self._port))
            self._should_connect = True
            self._connected = True
            print 'Connected to host: ' + self._ip + ":" + str(self._port)
        except:
            print 'Could not connect to host: ' + self._ip + ":" + str(self._port)
            self._should_connect = False
            self._connected = False

class Client(object):

    def __init__(self, locations):
        self._hosts = [ Host(location) for location in locations ]

    def _check_connections(self):
        for host in self._hosts:
            if host._should_connect and not host._connected:
                try:
                    host._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    host._socket.connect((host._ip, host._port))
                    host._connected = True
                except:
                    host._connected = False

    def put_pixels(self, pixels, channel=0):
        self._check_connections()
        len_hi_byte = (len(pixels) * 3) / 256
        len_lo_byte = (len(pixels) * 3) % 256
        message = chr(channel) + chr(0) + chr(len_hi_byte) + chr(len_lo_byte) + pixels.tobytes()
        
        for host in self._hosts:
            if host._should_connect:
                try:
                    host._socket.send(message)
                except:
                    host._connected = False

