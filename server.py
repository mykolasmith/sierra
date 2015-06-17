import time
import opc
import numpy as np

from handler import Handler

FPS = 1/60.
NUM_PIXELS = 300

class Universe(object):

    def __init__(self, client, strips, controllers):
        print 'Starting Universe...'
        
        handler = Handler(strips, controllers)
        controllers.bind(handler)
        
        while True:
            
            for controller in controllers.itervalues():
                controller.listen()
                
            now = time.time()
            handler.note_on(now)
            handler.note_off(now)
            handler.worker(now)
            
            for strip in strips:
                strip.aggregate()
            
            handler.expire()
            
            if client.connected and time.time() - client.last >= 1/60.:
                pixels = np.concatenate([
                    strip.pixels[:NUM_PIXELS].astype(np.uint8)
                    if len(strip.pixels) >= NUM_PIXELS
                    else np.concatenate([ strip.pixels, np.zeros((NUM_PIXELS - strip.length, 3)) ]).astype(np.uint8)
                    for strip in strips
                ])
                client.last = time.time()
                client.bus.put_pixels(pixels)
        
class Client(object):
    
    def __init__(self, location, strips):
        self.bus = opc.Client(location)
        self.strips = strips
        self.last = time.time()
        
        if self.bus.can_connect():
            print 'Connected to client: {0}'.format(location)
            self.connected = True
        else:
            print 'Not connected to client: {0}'.format(location)
            self.connected = False