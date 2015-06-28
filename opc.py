import socket
import numpy as np

class Host(object):
    
    def __init__(self, server_ip_port):

        self._ip, self._port = server_ip_port.split(':')
        self._port = int(self._port)
        
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self._ip, self._port))
            self._should_connect = True
            self._connected = True
        except:
            self._should_connect = False
            self._connected = False

class Client(object):

    def __init__(self, locations):
        """Create an OPC client object which sends pixels to an OPC server.

        server_ip_port should be an ip:port or hostname:port as a single string.
        For example: '127.0.0.1:7890' or 'localhost:7890'

        There are two connection modes:
        * In long connection mode, we try to maintain a single long-lived
          connection to the server.  If that connection is lost we will try to
          create a new one whenever put_pixels is called.  This mode is best
          when there's high latency or very high framerates.
        * In short connection mode, we open a connection when it's needed and
          close it immediately after.  This means creating a connection for each
          call to put_pixels. Keeping the connection usually closed makes it
          possible for others to also connect to the server.

        A connection is not established during __init__.  To check if a
        connection will succeed, use can_connect().

        If verbose is True, the client will print debugging info to the console.

        """
        
        self._hosts = []
        
        for location in locations:
            h = Host(location)
            self._hosts.append(h)

    def _check_connection(self):
        """Set up a connection if one doesn't already exist.

        Return True on success or False on failure.

        """
        for host in self._hosts:
            if host._should_connect and not host._connected:
                print 'Reconnecting to: ' + host._ip + ":" + str(host._port)
                try:
                    host._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    host._socket.connect((host._ip, host._port))
                    host._connected = True
                except:
                    pass

    def put_pixels(self, pixels, channel=0):
        """Send the list of pixel colors to the OPC server on the given channel.

        channel: Which strand of lights to send the pixel colors to.
            Must be an int in the range 0-255 inclusive.
            0 is a special value which means "all channels".

        pixels: A list of 3-tuples representing rgb colors.
            Each value in the tuple should be in the range 0-255 inclusive. 
            For example: [(255, 255, 255), (0, 0, 0), (127, 0, 0)]
            Floats will be rounded down to integers.
            Values outside the legal range will be clamped.

        Will establish a connection to the server as needed.

        On successful transmission of pixels, return True.
        On failure (bad connection), return False.

        The list of pixel colors will be applied to the LED string starting
        with the first LED.  It's not possible to send a color just to one
        LED at a time (unless it's the first one).

        """
        
        self._check_connection()

        # build OPC message
        len_hi_byte = (len(pixels) * 3) / 256
        len_lo_byte = (len(pixels) * 3) % 256
        message = chr(channel) + chr(0) + chr(len_hi_byte) + chr(len_lo_byte) + pixels.tobytes()
        
        for host in self._hosts:
            if host._should_connect:
                try:
                    host._socket.send(message)
                except:
                    host._connected = False

