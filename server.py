import time
import opc
import numpy as np
import socket

from strip import Strip
from handler import Handler
from controller import MasterController, MidiController, OSCController

from animations.motion_tween import MotionTween, BackwardMotionTween
from animations.positional   import Positional
from animations.perlin       import Perlin
from animations.clear_osc    import ClearOSC

NUM_PIXELS = 300
FPS = 1/60.

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
    
    def __init__(self, location, strips, local=False):
        self.bus = opc.Client(location)
        self.local = local
        self.strips = strips
        self.last = time.time()
        
        if self.bus.can_connect():
            print 'Connected to client: {0}'.format(location)
            self.connected = True
        else:
            print 'Not connected to client: {0}'.format(location)
            self.connected = False
        
if __name__ == '__main__':
    
    strips = tuple( Strip(x) for x in [NUM_PIXELS] * 48 )
        
    #client = Client("beaglebone.local:7890", strips)
    client = Client("localhost:7890", strips)
    
    total_pixels = 0
    for strip in strips:
        total_pixels += strip.length
        
    total_strips = 0
    for strip in strips:
        if not strip.length == 1:
            total_strips += 1
            
    print 'Total strips in universe: {0}'.format(total_strips)
    print 'Total pixels in universe: {0}'.format(total_pixels)
    
    controllers = MasterController({
       'midi': MidiController("IAC Driver Bus 1"),
       'osc':  OSCController(socket.gethostbyname(socket.gethostname()), 7000),
       #'nexus': MidiController("IAC Driver Bus 2"),
    })
    
    controllers['midi'].add_trigger(
        [60],
        channel=1,
        animation=MotionTween,
        strips=strips
    )
    
    controllers['midi'].add_trigger(
        [62],
        channel=1,
        animation=Perlin,
        strips=strips
    )
    
    universe = Universe(client, strips, controllers)
