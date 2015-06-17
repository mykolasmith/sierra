import time
import opc
import numpy as np

from handler import Handler

class Universe(object):

    def __init__(self, client, strips, controllers, num_pixels=300, fps=1/60.):
        print 'Total pixels per channel: {0}'.format(num_pixels)
        print 'Starting Universe...'
        
        handler = Handler(strips, controllers)
        controllers.bind(handler)
        
        for strip in strips:
            strip.pixels.resize((num_pixels,3))
        
        while True:
            
            for controller in controllers.itervalues():
                controller.listen()
            
            now = time.time()
            handler.note_on(now)
            handler.note_off(now)
            handler.worker(now)
            
            if client.connected and time.time() - client.last >= fps:

                for strip in strips:
                    strip.aggregate()
                
                client.bus.put_pixels(np.concatenate([
                    strip.pixels.astype(np.uint8)
                    for strip in strips
                ])[:21845])
                client.last = time.time()
                
            handler.expire()
            
        
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