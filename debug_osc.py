import sys
import socket
import time

from OSC import OSCServer

ip = socket.gethostbyname(socket.gethostname())
server = OSCServer( (ip, 7000) )

def callback(path, tags, args, source):
    print path, tags, args, source

while True:
    server.noCallback_handler = callback
    time.sleep(1)
    server.handle_request()