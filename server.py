import time
import opc
import numpy as np

import gevent
from gevent.queue import Queue

from controller import MidiController
from mapping import MidiMapping
from strip import Strip

from animations import MotionTween, Fade, Positional, Clear
        
class Universe(object):
    
    def __init__(self, client, strips, controllers):
        print 'Starting Universe...'
        self.client = client
        self.strips = strips
        self.controllers = controllers
        
        self.tasks = Queue()
        self.expire = Queue()
        self.greenlets = []
        
        start = []
        
        for controller in self.controllers.itervalues():
            start.append(gevent.spawn(controller.listener))
            
        for strip in self.strips:
            start.append(gevent.spawn(strip.aggregator))
            start.append(gevent.spawn(strip.worker))
            start.append(gevent.spawn(strip.firing))
            start.append(gevent.spawn(strip.expiry))
            #greenlets.append(gevent.spawn(strip.print_events))
            
        start.append(gevent.spawn(self.writer))
        
        gevent.joinall(start)
    
    def writer(self):
        MAX = 300
        while True:
            frames = [
                strip.frame[:MAX]
                if len(strip.frame) >= MAX
                else np.concatenate(
                    [strip.frame, np.zeros((MAX - strip.length,3)) ]
                )
                for strip in self.strips ]
            self.client.put_pixels(np.concatenate(frames), channel=0)
            gevent.sleep(1/80.)
            
if __name__ == '__main__':
    connected = False
    client = opc.Client("beaglebone.local:7890")
    
    if client.can_connect():
        print 'Connected to Beaglebone...'
    
    strips = [
        Strip(120),
        Strip(300),
        Strip(300),
        #Strip(300),
        #Strip(300),
        #Strip(300),
        #Strip(300),
        #Strip(300),
    ]
    
    ALL =    strips
    FIRST =  strips[0]
    SECOND = strips[1]
    THIRD =  strips[2]
    
    mpk49 = MidiController("IAC Driver Bus 1")
    mapping = MidiMapping(mpk49)
    
    # MPK Mappings
    
    F1 = 12
    F2 = 13
    F3 = 14
    F4 = 15
    F5 = 16
    F6 = 17
    
    K1 = 2
    K2 = 3
    K3 = 4
    K4 = 5
    K5 = 6
    K6 = 7
    K7 = 8
    K8 = 9
    
    S1 = 21
    S2 = 22
    S3 = 23
    S4 = 24
    S5 = 25
    S6 = 26
    S7 = 27
    S8 = 28
    
    # MotionTween
    
    mapping.add(strips=ALL,
                channel=1,
                animation=MotionTween,
                notes=[60],
                inputs=[K1,F1,S1],
                master=True,
                pitchwheel=True)
    mapping.add(strips=[FIRST],
                channel=1,
                animation=MotionTween,
                notes=[62],
                inputs=[K2,F2,S2],
                master=True,
                pitchwheel=True)
    mapping.add(strips=[THIRD],
                channel=1,
                notes=[64],
                animation=MotionTween,
                inputs=[K3,F3,S3],
                master=True,
                pitchwheel=True)
    mapping.add(strips=[SECOND],
                channel=1,
                notes=[65],
                animation=MotionTween,
                inputs=[K4,F4,S4],
                master=True,
                pitchwheel=True)
                
    #mapping.add(strips=strips[3:8],
    #            channel=1,
    #            notes=[67],
    #            animation=MotionTween,
    #            inputs=[K6,F6,S6],
    #            master=True,
    #            pitchwheel=True)
                
    # Positional

    mapping.add(strips=ALL,
                channel=1,
                notes=xrange(36,59),
                animation=Positional,
                inputs=[K5,F5,S5],
                master=True)
    
    # Clear
                
    mapping.add(strips=FIRST,
                channel=1,
                notes=[79],
                animation=Clear)
                
    mapping.add(strips=ALL,
                channel=1,
                notes=[81],
                animation=Clear)
        
    mapping.add(strips=THIRD,
                channel=1,
                notes=[83],
                animation=Clear)
    
    controllers = {
        'mpk49' : mpk49
    }
    
    universe = Universe(client, strips, controllers)
