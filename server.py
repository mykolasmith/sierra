import time
import opc
import numpy as np

from controller import MidiController, MixerController
from mapping import MidiMapping
from strip import Strip
from consts import *

from animations import MotionTween, Positional

class Universe(object):
    
    def __init__(self, client, strips, controllers):
        print 'Starting Universe...'
        self.client = client
        self.strips = strips
        self.controllers = controllers
        self.last_push = time.time()
        
        while True:
            for controller in self.controllers.itervalues():
                controller.listen()
            
            now = time.time()
            for strip in self.strips:
                strip.handle_expire()
                strip.handle_note_on()
                strip.handle_note_off()
                strip.worker(now)
            
            if now - self.last_push >=  1/80.:
                for strip in self.strips:
                    strip.aggregate()
                self.writer()
                self.last_push = now
    
    def writer(self):
        # OK, this is the slight caveat:
        #   Since LEDscape is optimized to receive a single frame
        #   consisting of the entire frame buffer,
        #   that is a consistent length (e.g. 8 strips, 300 leds each),
        #   we need to fill some blank indices,
        #   when a srip is shorter than the max.
        # There might be a better way to do this with numpy. TODO
        MAX = 300
        pixels = [
            strip.pixels[:MAX]
            if len(strip.pixels) >= MAX
            else np.concatenate([ strip.pixels, np.zeros((MAX - strip.length, 3)) ])
            for strip in self.strips
        ]
        self.client.put_pixels(np.concatenate(pixels))

if __name__ == '__main__':
    # Open connection to the OPC client.
    #client = opc.Client("beaglebone.local:7890")
    client = opc.Client("localhost:7890")
    if client.can_connect():
        print 'Connected to Beaglebone...'
    
    # Declare length of each strip.
    # There is absolutely no geometry support yet. TODO
    # Index refers to the beaglebone channel (0-48).
    strips = [
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
        Strip(300),
    ]
    
    print 'Total number of strips: {0}'.format(len(strips))
    
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
                strips=strips,
                inputs=[F1,K1,S1,F8,S6],
                master=True,
                pitchwheel=True)
                
    # When any note between 36 and 59 on channel 1 is pressed
    # Run a Positional animation class
    # This is how I do something like playing a chord
    # To have the corresponding indices light up
    mapping.add(notes=xrange(36,59),
                channel=1,
                animation=Positional,
                strips=strips,
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
    
    universe = Universe(client, strips, controllers)
