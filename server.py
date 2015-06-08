import time
import opc
import numpy as np

from strip import Strip
from handler import Handler
from consts import MPK49_MAPPINGS, NEXUS_MAPPINGS
from controller import MasterController, MidiController, OSCController

from animations.motion_tween import MotionTween
from animations.positional import   Positional
from animations.perlin import       Perlin

NUM_PIXELS = 300
FPS = 1/60.

class Universe(object):

    def __init__(self, clients, strips, controllers):
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
           
            for client in clients:
                if client.connected:
                    pixels = np.concatenate([
                        strip.pixels[:NUM_PIXELS].astype(np.uint8)
                        if len(strip.pixels) >= NUM_PIXELS
                        else np.concatenate([ strip.pixels, np.zeros((NUM_PIXELS - strip.length, 3)) ]).astype(np.uint8)
                        for strip in client.strips
                    ])
                    client.bus.put_pixels(pixels)
            
            time.sleep(FPS)
        
class Client(object):
    
    def __init__(self, location, strips, local=False):
        self.bus = opc.Client(location)
        self.local = local
        self.strips = strips
        
        if self.bus.can_connect():
            print 'Connected to client: {0}'.format(location)
            self.connected = True
        else:
            print 'Not connected to client: {0}'.format(location)
            self.connected = False
        
if __name__ == '__main__':
    
    strips = tuple( Strip(x) for x in [NUM_PIXELS] * 48 )
    
    simulation = Client("localhost:7890", strips)
    #beaglebone = Client("beaglebone.local:7890", strips)
    
    clients = (
        simulation,
        #beaglebone,
    )
    
    total_pixels = 0
    for strip in strips:
        total_pixels += strip.length
        
    total_strips = len(strips)
            
    print 'Total strips in universe: {0}'.format(total_strips)
    print 'Total pixels in universe: {0}'.format(total_pixels)
    
    mpk49 = MidiController("IAC Driver Bus 1")
    osc = OSCController("10.0.9.177", 7000)
    #nexus = MidiController("IAC Driver Bus 2")
    
    
    osc.add_trigger(
        '/multipush1/1/16',
        channel=1,
        animation=Positional,
        strips=strips
    )
    
    mpk49.add_trigger(
        [60],
        channel=1,
        animation=MotionTween,
        strips=strips)
        
    mpk49.add_trigger(
        [62],
        channel=1,
        animation=MotionTween,
        strips=strips)
    
    mpk49.add_trigger(
        xrange(36,50),
        channel=1,
        animation=Positional,
        strips=strips,
    )
    
    mpk49.add_trigger(
        [64],
        channel=1,
        animation=Perlin,
        strips=strips,
    )
   
    controllers = MasterController({
        'mpk49' : mpk49,
        'ipad' : osc
        #'nexus' : nexus
    })
    
    universe = Universe(clients, strips, controllers)
