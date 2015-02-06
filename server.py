import time
import opc
import gevent
from gevent.queue import Queue

from controller import MidiController
from mapping import MidiMapping
from strip import Strip

from animations import MotionTween, Fade, Positional
        
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
            if self.pending_tasks:
                gevent.joinall(self.pending_tasks)
                self.pending_tasks = []
            gevent.sleep(time.time() - t0)
            
    def expiry_scheduler(self):
        while True:
            t0 = time.time()
            while not self.expire.empty():
                expiry = self.expire.get()
                gevent.kill(expiry.parent)
                expire = gevent.spawn(expiry.off)
                self.pending_expiry.append(expire)
            gevent.sleep(time.time() - t0)
            
    def expiry_handler(self):
        while True:
            t0 = time.time()
            if self.pending_expiry:
                gevent.joinall(self.pending_expiry)
                self.pending_expiry = []
            gevent.sleep(time.time() - t0)
        
    def writer(self):
        while True:
            for channel, strip in self.strips.iteritems():
                try:
                    self.client.put_pixels(strip.frame, channel)
                except:
                    pass
            gevent.sleep(1/90.)
            
if __name__ == '__main__':
    connected = False
    client = opc.Client("beaglebone.local:7890")
    
    if client.can_connect():
        print 'Connected to Beaglebone...'
    
    strips = {
        1: Strip(120),
        2: Strip(300)
    }
    
    group1 = [strips.get(1), strips.get(2)]
    
    mpk49 = MidiController("IAC Driver Bus 1")
    mapping = MidiMapping(mpk49)
    
    F1 = 12
    F2 = 13
    F3 = 14
    F4 = 15
    F5 = 16
    F6 = 17
    
    mapping.add(strips=[strips.get(1)],
                channel=1,
                animation=MotionTween,
                notes=[60],
                inputs=[F1,F2,F3],
                master=True,
                pitchwheel=True)
    mapping.add(strips=[strips.get(2)],
                channel=1,
                animation=MotionTween,
                notes=[62],
                inputs=[F1,F2,F3],
                master=True,
                pitchwheel=True)
    mapping.add(strips=[strips.get(1)],
                channel=1,
                notes=[64],
                animation=Fade)
    mapping.add(strips=group1,
                channel=1,
                notes=xrange(36,59),
                animation=Positional,
                inputs=[F4,F5,F6])
    
    controllers = {
        'mpk49' : mpk49
    }
    
    universe = Universe(client, strips, controllers)
