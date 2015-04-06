import time
import opc
import numpy as np

from controller import MidiController, MixerController
from mapping import MidiMapping
from strip import Strip
from consts import *

from animations import MotionTween, Positional, Rainbow

class Universe(object):
    
    def __init__(self, beaglebones, controllers):
        print 'Starting Universe...'
        self.beaglebones = beaglebones
        self.controllers = controllers
        self.last_push = time.time()
        
        while True:
            for controller in self.controllers.itervalues():
                controller.listen()
            
            now = time.time()
            for beaglebone in self.beaglebones.itervalues():
                for strip in beaglebone.strips:
                    strip.handle_note_on()
                    strip.handle_note_off()
                    strip.worker(now)
            
            if time.time() - self.last_push >=  1/80.:
                for strip in beaglebone.strips:
                    strip.aggregate()
                    strip.handle_expire()
                self.writer()
                self.last_push = time.time()
            
    def writer(self):
        # OK, this is the slight caveat:
        #   Since LEDscape is optimized to receive a single frame
        #   consisting of the entire frame buffer,
        #   that is a consistent length (e.g. 8 strips, 600 leds each),
        #   we need to fill some blank indices,
        #   when a srip is shorter than the max.
        # There might be a better way to do this with numpy. TODO
        MAX = 300
        for beaglebone in self.beaglebones.itervalues():
            beaglebone.client.put_pixels(np.concatenate([
                strip.pixels[:MAX].astype(np.uint8)
                if len(strip.pixels) >= MAX
                else np.concatenate([ strip.pixels, np.zeros((MAX - strip.length, 3)) ]).astype(np.uint8)
                for strip in beaglebone.strips
            ])[:21845]) # OPC can only handle 21,845 pixels at a time.
        
class Client(object):
    
    def __init__(self, location, strips):
        self.strips = strips
        self.client = opc.Client(location)
        if self.client.can_connect():
            print 'Connected to Beaglebone at: {0}'.format(location)
        
if __name__ == '__main__':
    # Open connection to the OPC client.
    #client = opc.Client("beaglebone.local:7890")
    
    # Declare length of each strip.
    # There is absolutely no geometry support yet. TODO
    # Index refers to the beaglebone channel (0-48).
    strips1 = [ Strip(x) for x in [300] * 48 ]
    strips2 = [ Strip(x) for x in [300] * 48 ]
    
    local = Client("localhost:7890", strips1)
    #bbb1 = Client("beaglebone1.local", strips1)
    #bbb2 = Client("beaglebone2.local", strips2)
    
    clients = {
        0 : local,
        #1 : bbb1,
        #2 : bbb2
    }
    
    # Create a MIDI controller and declare which MIDI port to listen on.
    mpk49 = MidiController("IAC Driver Bus 1")
    
    # Add a note->animation mapping for the controller.
    mapping = MidiMapping(mpk49)
    
    # This part is a bit tedious.
    # Thinking about doing a spatially aware mapping GUI using my Project Tango. TODO
    
    # When channel 1, note 60 is pressed
    # Run a MotionTween animation class
    # Across all the strips
    # Using a variety of the MPK49's inputs
    # With respect to the master brightness
    # And the pitchweel's position
    mapping.add(notes=[60],
                channel=1,
                animation=MotionTween,
                strips=strips1,
                inputs=[F1,K1,S1,F8,S6],
                master=True,
                pitchwheel=True)
                
    mapping.add(notes=[62],
                channel=1,
                animation=MotionTween,
                strips=strips1,
                inputs=[F1,K1,S1,F8,S6],
                master=True,
                pitchwheel=True)
                
    mapping.add(notes=[64],
                channel=1,
                animation=Rainbow,
                strips=strips1)
                
    # When any note between 36 and 59 on channel 1 is pressed
    # Run a Positional animation class
    # This is how I do something like playing a chord
    # To have the corresponding indices light up
    mapping.add(notes=xrange(36,59),
                channel=1,
                animation=Positional,
                strips=strips1,
                inputs=[F2,K2,S6],
                master=True)
                
    # OK, this is ghetto.
    # But I wanted a way use parameters from a DJM-900,
    # So I'm passing those values into the MPK49's "globals".
    # Since I don't really have animations working w/ multiple MIDI controllers yet. TODO
    # nexus = MixerController("DJM-900nexus", mpk49)
     
    controllers = {
        'mpk49' : mpk49,
    #    'nexus' : nexus
    }
    
    universe = Universe(clients, controllers)
