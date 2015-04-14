import time
import opc
import numpy as np

from strip import Strip
from consts import MPK49_MAPPINGS
from controller import MasterController, MidiController

from animations import MotionTween, Positional, Rainbow

# Per LEDscape spec, all strips must be of equal length
NUM_PIXELS = 300

class Universe(object):

    def __init__(self, clients, controllers):
        print 'Starting Universe...'
        self.clients = clients
        self.controllers = controllers
        
        for client in self.clients:
            for strip in client.strips:
                strip.bind(self.controllers)
        
        while True:
            for controller in self.controllers.itervalues():
                controller.listen()
            
            now = time.time()
            for client in self.clients:
                
                for strip in client.strips:
                    strip.handle_note_on(now)
                    strip.handle_note_off(now)
                    strip.worker(now)
            
                for strip in client.strips:
                    strip.aggregate()
                    strip.handle_expire()
                    
                if now - client.last_push >= 1/60.0:
                    pixels = np.concatenate([
                        strip.pixels[:NUM_PIXELS].astype(np.uint8)
                        if len(strip.pixels) >= NUM_PIXELS
                        else np.concatenate([ strip.pixels, np.zeros((NUM_PIXELS - strip.length, 3)) ]).astype(np.uint8)
                        for strip in client.strips
                    ])[:21845]
                    
                    client.bus.put_pixels(pixels)
                    client.last_push = now
        
class Client(object):
    
    def __init__(self, location, strips, local=False):
        self.bus = opc.Client(location)
        self.local = local
        self.strips = strips
        self.last_push = time.time()
        
        if self.bus.can_connect():
            print 'Connected to client: {0}'.format(location)
        else:
            print 'Not connected to client: {0}'.format(location)
        
if __name__ == '__main__':
    
    strips = tuple( Strip(x) for x in [NUM_PIXELS] * 48 )
    
    #simulation = Client("localhost:7890", strips, local=True)
    beaglebone = Client("beaglebone.local:7890", strips)
    
    clients = (
        #simulation,
        beaglebone,
    )
    
    total_pixels = 0
    for client in clients:
        if not client.local:
            for strip in client.strips:
                total_pixels += strip.length
            
    total_strips = 0
    for client in clients:
        if not client.local:
            total_strips += len(client.strips)
            
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
    
    universe = Universe(clients, controllers)
