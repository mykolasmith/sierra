import time
import opc
import numpy as np

import gevent
from gevent.queue import Queue

from controller import MidiController, MixerController
from mapping import MidiMapping
from strip import Strip
from consts import *

from animations import MotionTween, Positional, Clear

class Universe(object):
    
    def __init__(self, client, strips, controllers):
        print 'Starting Universe...'
        self.client = client
        self.strips = strips
        self.controllers = controllers
        
        # This is the main event loop. A list of coroutines to cycle between.
        start = []
        
        # Start the listeners for each MIDI controller (controller.py)
        for controller in self.controllers.itervalues():
            start.append(gevent.spawn(controller.listener))
            
        
        for strip in self.strips:
            # Aggegator combines animation frames into 1 strip frame
            start.append(gevent.spawn(strip.aggregator))
            # The worker delegates note_on/note_off actions to the event loop
            start.append(gevent.spawn(strip.worker))
            # Firing prepares new task for note_on 
            start.append(gevent.spawn(strip.firing))
            # Expiry ends an active event
            start.append(gevent.spawn(strip.expiry))
            
        # The writer sends all frames to the network layer
        start.append(gevent.spawn(self.writer))
        
        # Starts the main event loop
        gevent.joinall(start)
    
    def writer(self):
        # OK, this is the slight caveat:
        #   Since LEDscape is optimized to receive a single frame
        #   consisting of the entire frame buffer,
        #   that is a consistent length (e.g. 8 strips, 300 leds each),
        #   we need to fill some blank indices,
        #   when a srip is shorter than the max.
        # There might be a better way to do this with numpy. TODO
        MAX = 300
        while True:
            frames = [
                strip.frame[:MAX]
                if len(strip.frame) >= MAX
                else np.concatenate(
                    [ strip.frame, np.zeros((MAX - strip.length, 3)) ]
                )
                for strip in self.strips ]
            self.client.put_pixels(np.concatenate(frames))
            gevent.sleep(1/80.)

if __name__ == '__main__':
    # Open connection to the OPC client.
    client = opc.Client("beaglebone.local:7890")
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
    ]
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
                inputs=[F1,K1,S1,S6,F8],
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
                inputs=[F4,K4,S8],
                master=True)
                
    # I like having one note that I can hit
    # That clears everything
    mapping.add(notes=[84],
                channel=1,
                animation=Clear,
                strips=strips)
                
    # OK, this is ghetto.
    # But I wanted a way use parameters from a DJM-900,
    # So I'm passing those values into the MPK49's "globals".
    # Since I don't really have animations working w/ multiple MIDI controllers yet. TODO
    # nexus = MixerController("DJM-900nexus", mpk49)
    
    # With the current setup, you can use any device as long as it's broadcasting over the IAC driver.
    # But if you include the nexus, it will throw an error unless a DJM-900 nexus is hooked up.
    # Kind of annoying. TODO
    controllers = {
        'mpk49' : mpk49,
    #    'nexus' : nexus
    }
    
    universe = Universe(client, strips, controllers)
