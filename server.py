import time
import opc
import numpy as np

from mapping import MidiMapping
from strip import Strip
from consts import MPK49_MAPPINGS
from controller import MasterController, MidiController

from animations import MotionTween, Positional, Rainbow

class Universe(object):

    def __init__(self, clients, controllers):
        print 'Starting Universe...'
        self.clients = clients
        self.controllers = controllers
        self.last_push = time.time()
        
        for client in self.clients.itervalues():
            for strip in client.strips:
                strip.bind(self.controllers)
        
        while True:
            for controller in self.controllers.itervalues():
                controller.listen()
            
            now = time.time()
            for client in self.clients.itervalues():
                for strip in client.strips:
                    strip.handle_note_on(now)
                    strip.handle_note_off(now)
                    strip.worker(now)
            
            if now - self.last_push >=  1/80.:
                for strip in client.strips:
                    strip.aggregate()
                    strip.handle_expire()
                self.writer()
                self.last_push = now
            
    def writer(self):
        # OK, this is the slight caveat:
        #   Since LEDscape is optimized to receive a single frame
        #   consisting of the entire frame buffer,
        #   that is a consistent length (e.g. 8 strips, 600 leds each),
        #   we need to fill some blank indices,
        #   when a srip is shorter than the max.
        # There might be a better way to do this with numpy. TODO
        MAX = 1000
        for client in self.clients.itervalues():
            client.bus.put_pixels(np.concatenate([
                strip.pixels[:MAX].astype(np.uint8)
                if len(strip.pixels) >= MAX
                else np.concatenate([ strip.pixels, np.zeros((MAX - strip.length, 3)) ]).astype(np.uint8)
                for strip in client.strips
            ])[:21845]) # OPC can only handle 21,845 pixels at a time.
            

        
class Client(object):
    
    def __init__(self, location, strips):
        self.strips = strips
        self.bus = opc.Client(location)
        if self.bus.can_connect():
            print 'Connected to client: {0}'.format(location)
        else:
            print 'Not connected to client: {0}'.format(location)
        
if __name__ == '__main__':
    # Open connection to the OPC client.
    #client = opc.Client("beaglebone.local:7890")
    
    # Declare length of each strip.
    # There is absolutely no geometry support yet. TODO
    # Index refers to the beaglebone channel (0-48).
    strips1 = [ Strip(x) for x in [455] * 48 ]
    strips2 = [ Strip(x) for x in [455] * 48 ]
    strips3 = [ Strip(x) for x in [455] * 48 ]
    strips4 = [ Strip(x) for x in [455] * 48 ]
    
    local = Client("localhost:7890", strips1 + strips2 + strips3 + strips4)
    #bbb1 = Client("beaglebone1.local:7890", strips1)
    #bbb2 = Client("beaglebone2.local:7890", strips2)
    
    clients = {
        0 : local,
        #1 : bbb1,
        #2 : bbb2
    }
    
    total_pixels = 0
    for client in clients.itervalues():
        for strip in client.strips:
            total_pixels += strip.length
            
    total_strips = 0
    for client in clients.itervalues():
        total_strips += len(client.strips)
            
    print 'Total strips in universe: {0}'.format(total_strips)
    print 'Total pixels in universe: {0}'.format(total_pixels)
    
    # Create a MIDI controller and declare which MIDI port to listen on.
    mpk49 = MidiController("IAC Driver Bus 1", MPK49_MAPPINGS)
    nexus = MidiController("IAC Driver Bus 2")
    
    mpk49.add_trigger(
        notes=[60],
        channel=1,
        animation=MotionTween,
        strips=strips1
    )
    
    mpk49.add_trigger(
        notes=xrange(36,59),
        channel=1,
        animation=Positional,
        strips=strips1
    )
    
    mpk49.add_trigger(
        notes=[62],
        channel=1,
        animation=Rainbow,
        strips=strips1
    )
   
    controllers = MasterController({
        'mpk49' : mpk49,
        'nexus' : nexus
    })
    
    universe = Universe(clients, controllers)
