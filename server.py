import time
import opc
import numpy as np

from strip import Strip
from handler import Handler
from consts import MPK49_MAPPINGS, NEXUS_MAPPINGS
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
    
    mpk49 = MidiController("IAC Driver Bus 1")
    osc = OSCController("169.254.87.176", 7000)
    #nexus = MidiController("IAC Driver Bus 2")
    
    strips = (
        # STAGE 1, Receiver 1
        Strip(300), Strip(1), Strip(1), Strip(1),
        # Stage 1, Receiver 2
        Strip(300), Strip(300), Strip(300), Strip(1),
        # Stage 1, Receiver 3
        Strip(300), Strip(300), Strip(1), Strip(1),
        ###
        # Stage 2, Receiver 1
        Strip(300), Strip(300), Strip(1), Strip(1),
        # Stage 2, Receiver 2
        Strip(300), Strip(300), Strip(300), Strip(1),
        # Stage 2, Receiver 3
        Strip(300), Strip(1), Strip(1), Strip(1),
    )
    
    GOAL1 = [
        strips[0],
        strips[4],
        strips[5]
    ]
    
    GOAL2 = [
        strips[6],
        strips[8],
        strips[9],
    ]
    
    GOAL3 = [
        strips[12],
        strips[13],
        strips[16]
    ]
    
    GOAL4 = [
        strips[17],
        strips[18],
        strips[20]
    ]
 
    ALL_GOALS = GOAL1 + GOAL2 + GOAL3 + GOAL4
    
     # DRUM PADS
    
    mpk49.add_trigger(
        [45],
        channel=1,
        animation=MotionTween,
        strips=GOAL2)
        
    mpk49.add_trigger(
        [42],
        channel=1,
        animation=BackwardMotionTween,
        strips=GOAL2)
    
    mpk49.add_trigger(
        [39],
        channel=1,
        animation=MotionTween,
        strips=GOAL1)

    mpk49.add_trigger(
        [36],
        channel=1,
        animation=BackwardMotionTween,
        strips=GOAL1)
        
    mpk49.add_trigger(
        [47],
        channel=1,
        animation=MotionTween,
        strips=GOAL3)
        
    mpk49.add_trigger(
        [44],
        channel=1,
        animation=BackwardMotionTween,
        strips=GOAL3)
        
    mpk49.add_trigger(
        [41],
        channel=1,
        animation=MotionTween,
        strips=GOAL4)
        
    mpk49.add_trigger(
        [38],
        channel=1,
        animation=BackwardMotionTween,
        strips=GOAL4)
        
    mpk49.add_trigger(
        [46],
        channel=1,
        animation=MotionTween,
        strips=ALL_GOALS)
        
    mpk49.add_trigger(
        [43],
        channel=1,
        animation=BackwardMotionTween,
        strips=ALL_GOALS)
        
    # KEYS
    
    mpk49.add_trigger(
        [53],
        channel=1,
        animation=Perlin,
        strips=ALL_GOALS,
    )
    
    mpk49.add_trigger(
        xrange(60,76),
        channel=1,
        animation=Positional,
        strips=ALL_GOALS,
    )
    
    # MISC
    
    mpk49.add_trigger(
        [84],
        channel=1,
        animation=ClearOSC,
        strips=[strips[0]])
    
    # touchOSC
    
    osc.add_trigger(
        '/multipush1/1/16',
        channel=1,
        animation=Positional,
        strips=ALL_GOALS
    )
    
    osc.add_trigger(
        '/multipush2/16/1',
        channel=1,
        animation=Positional,
        strips=GOAL1 + GOAL2)
    
    osc.add_trigger(
        '/multipush3/16/1',
        channel=1,
        animation=Positional,
        strips=GOAL3 + GOAL4)

    osc.add_trigger(
        '/push1',
        channel=1,
        animation=ClearOSC,
        strips=[strips[0]])
        
    osc.add_trigger(
        '/multipush3/1/16',
        channel=1,
        animation=Positional,
        strips=GOAL3 + GOAL4)
        
    osc.add_trigger(
        '/push1',
        channel=2,
        animation=MotionTween,
        strips=GOAL1)
        
    osc.add_trigger(
        '/push2',
        channel=2,
        animation=BackwardMotionTween,
        strips=GOAL1)
        
    osc.add_trigger(
        '/push3',
        channel=2,
        animation=MotionTween,
        strips=GOAL2)
        
    osc.add_trigger(
        '/push4',
        channel=2,
        animation=BackwardMotionTween,
        strips=GOAL2)
    
    osc.add_trigger(
        '/push5',
        channel=2,
        animation=MotionTween,
        strips=GOAL3)
        
    osc.add_trigger(
        '/push6',
        channel=2,
        animation=BackwardMotionTween,
        strips=GOAL3)
        
    osc.add_trigger(
        '/push7',
        channel=2,
        animation=MotionTween,
        strips=GOAL4)
        
    osc.add_trigger(
        '/push8',
        channel=2,
        animation=BackwardMotionTween,
        strips=GOAL4)
        
    osc.add_trigger(
        "/push10",
        channel=2,
        animation=Perlin,
        strips=ALL_GOALS
    )
    
    osc.add_trigger(
        '/push9',
        channel=2,
        animation=ClearOSC,
        strips=[strips[0]])
   
    controllers = MasterController({
        'mpk49' : mpk49,
        'ipad' : osc
        #'nexus' : nexus
    })
    
    universe = Universe(client, strips, controllers)
