import time
import opc
import numpy as np

from strip import Strip
from handler import Handler
from consts import MPK49_MAPPINGS
from controller import MasterController, MidiController

from animations import MotionTween, Positional, Rainbow

# Per LEDscape spec, all strips must be of equal length
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
            handler.handle_note_on(now)
            handler.handle_note_off(now)
            handler.worker(now)
            
            #handler.print_active()
            
            for strip in strips:
                strip.aggregate()
                
            handler.handle_expire()
            
            for client in clients:
                if client.connected and now - client.last_push >= FPS:
                        client.bus.put_pixels(
                            np.concatenate([
                                strip.pixels[:NUM_PIXELS].astype(np.uint8)
                                if len(strip.pixels) >= NUM_PIXELS
                                else np.concatenate([ strip.pixels, np.zeros((NUM_PIXELS - strip.length, 3)) ]).astype(np.uint8)
                                for strip in client.strips
                            ])[:21845]
                        )
                        
                        client.last_push = now
        
class Client(object):
    
    def __init__(self, location, strips, local=False):
        self.bus = opc.Client(location)
        self.local = local
        self.strips = strips
        self.last_push = time.time()
        
        if self.bus.can_connect():
            print 'Connected to client: {0}'.format(location)
            self.connected = True
        else:
            print 'Not connected to client: {0}'.format(location)
            self.connected = False
        
if __name__ == '__main__':
    
    #strips = tuple( Strip(x) for x in [NUM_PIXELS] * 48 )
    strips = tuple( Strip(x) for x in [15, 30, 60, 120, 160, 180, 200, 240, 260, 300 ] * 65 )
    
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
    
    mpk49 = MidiController("IAC Driver Bus 1", MPK49_MAPPINGS)
    nexus = MidiController("IAC Driver Bus 2")
    
    mpk49.add_trigger(
        notes=[60],
        channel=1,
        animation=MotionTween,
        strips=strips
    )
    
    mpk49.add_trigger(
        notes=xrange(36,59),
        channel=1,
        animation=Positional,
        strips=strips
    )
    
    mpk49.add_trigger(
        notes=[62],
        channel=1,
        animation=Rainbow,
        strips=strips
    )
   
    controllers = MasterController({
        'mpk49' : mpk49,
        'nexus' : nexus
    })
    
    universe = Universe(clients, strips, controllers)
