import time
import opc
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
        
        self.pending_tasks = []
        self.pending_expiry = []
        
        gevent.joinall([
            gevent.spawn(self.start),
            gevent.spawn(self.firing_scheduler),
            gevent.spawn(self.firing_handler),
            gevent.spawn(self.expiry_scheduler),
            gevent.spawn(self.expiry_handler),
            gevent.spawn(self.writer)
        ])
        
    def start(self):
        gevent.joinall(
            [ gevent.spawn(controller.listener, self) for controller in self.controllers.itervalues()] +
            [ gevent.spawn(strip.aggregator) for strip in self.strips.itervalues()]
        )
        
    def firing_scheduler(self): 
        while True:
            t0 = time.time()
            while not self.tasks.empty():
                task = self.tasks.get()
                event = gevent.spawn(
                    task['animation'],
                    task['strip'],
                    task['controller'],
                    task['msg']
                )
                self.pending_tasks.append(event)
            gevent.sleep(time.time() - t0)
    
    def firing_handler(self):
        while True:
            t0 = time.time()
            gevent.joinall(self.pending_tasks)
            gevent.sleep(time.time() - t0)
            
    def expiry_scheduler(self):
        while True:
            t0 = time.time()
            while not self.expire.empty():
                expiry = self.expire.get()
                gevent.killall(expiry.greenlets)
                expire = gevent.spawn(expiry.off)
                self.pending_expiry.append(expire)
            gevent.sleep(time.time() - t0)
            
    def expiry_handler(self):
        while True:
            t0 = time.time()
            gevent.joinall(self.pending_expiry)
            gevent.sleep(time.time() - t0)
        
    def writer(self):
        while True:
            for channel, strip in self.strips.iteritems():
                self.client.put_pixels(strip.frame, channel)
            gevent.sleep(1/80.)
            
if __name__ == '__main__':
    connected = False
    client = opc.Client("beaglebone.local:7890")
    
    if client.can_connect():
        print 'Connected to Beaglebone...'
    
    strips = {
        1: Strip(120),
        2: Strip(300)
    }
    
    LEFT =  [strips.get(1)]
    RIGHT = [strips.get(2)]
    BOTH = LEFT + RIGHT
    
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
    
    mapping.add(strips=LEFT,
                channel=1,
                animation=MotionTween,
                notes=[60],
                inputs=[K1,F1,S1],
                master=True,
                pitchwheel=True)
    mapping.add(strips=BOTH,
                channel=1,
                animation=MotionTween,
                notes=[62],
                inputs=[K2,F2,S2],
                master=True,
                pitchwheel=True)
    mapping.add(strips=RIGHT,
                channel=1,
                notes=[64],
                animation=MotionTween,
                inputs=[K3,F3,S3],
                master=True,
                pitchwheel=True)
                
    # Positional

    mapping.add(strips=BOTH,
                channel=1,
                notes=xrange(36,59),
                animation=Positional,
                inputs=[K4,F4,S4],
                master=True)
    
    # Clear
                
    mapping.add(strips=LEFT,
                channel=1,
                notes=[79],
                animation=Clear)
                
    mapping.add(strips=BOTH,
                channel=1,
                notes=[81],
                animation=Clear)
        
    mapping.add(strips=RIGHT,
                channel=1,
                notes=[83],
                animation=Clear)
    
    controllers = {
        'mpk49' : mpk49
    }
    
    universe = Universe(client, strips, controllers)
