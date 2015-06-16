import sys
import socket
from time import sleep

from OSC import OSCServer

ip = socket.gethostbyname(socket.gethostname())
server = OSCServer( (ip, 7000) )

def callback(path, tags, args, source):
    # which user will be determined by path:
    # we just throw away all slashes and join together what's left
    print path, tags, args, source

# user script that's called by the game engine every frame
def each_frame():
    # clear timed_out flag
    server.timed_out = False
    # handle all pending requests then return
    while not server.timed_out:
        server.handle_request()

# simulate a "game engine"
while True:
    # do the game stuff:
    server.noCallback_handler = callback
    sleep(1)
    # call user script
    each_frame()

server.close()