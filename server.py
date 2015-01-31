import time
import opc
import gevent
from gevent.queue import Queue

from controller import MidiController
from mapping import MidiMapping
from strip import Strip

from animations import MotionTween, Fade, FullKeyboardPositional
        
class Universe(object):
    
    def __init__(self, client, strips, controllers):
        print 'Starting Universe...'
        self.client = client
        self.strips = strips
        self.controllers = controllers
        
        self.tasks = Queue()
        self.pending = []
        
        gevent.joinall([
            gevent.spawn(self.start),
            gevent.spawn(self.scheduler),
            gevent.spawn(self.handler),
            gevent.spawn(self.writer)
        ])
        
    def start(self):
        gevent.joinall(
            [ gevent.spawn(controller.listener, self) for controller in self.controllers.itervalues()] +
            [ gevent.spawn(strip.aggregator) for strip in self.strips.itervalues() ]
        )
        
    def scheduler(self): 
        while True:
            t0 = time.time()
            while not self.tasks.empty():
                task = self.tasks.get(timeout=0)
                event = gevent.spawn(
                    task['animation'],
                    task['strip'],
                    task['controller'],
                    task['msg']
                )
                self.pending.append(event)
            delta = time.time() - t0
            gevent.sleep(delta)
    
    def handler(self):
        while True:
            t0 = time.time()
            if self.pending:
                gevent.joinall(self.pending)
                self.pending = []
            delta = time.time() - t0
            gevent.sleep(delta)
        
    def writer(self):
        while True:
            for channel, strip in strips.iteritems():
                self.client.put_pixels(strip.frame, channel)
            gevent.sleep(1/240.)
            
if __name__ == '__main__':
    connected = False
    client = opc.Client("beaglebone.local:7890")
    
    if client.can_connect():
        print 'Connected to Beaglebone...'
    
    strips = {
        1: Strip(120),
        2: Strip(300)
    }
    
    group_1 = [strips.get(1), strips.get(2)]
    
    mpk49 = MidiController("IAC Driver Bus 1")
    mapping = MidiMapping()
    mpk49.bind(mapping)
    
    mapping.add(strips=[strips.get(1)],
                channel=1,
                notes=[60],
                animation=MotionTween,
                inputs=[12,13,14])
    mapping.add(strips=[strips.get(2)],
                channel=1,
                notes=[62],
                animation=MotionTween,
                inputs=[12,13,14])
    mapping.add(strips=group_1,
                channel=1,
                notes=[64],
                animation=Fade)
    mapping.add(strips=group_1,
                channel=1,
                notes=xrange(36,59),
                animation=FullKeyboardPositional,
                inputs=[15,16,17])
    
    controllers = {
        'mpk49' : mpk49
    }
    
    mappings = {
        'mpk49' : mapping
    }
    
    universe = Universe(client, strips, controllers)
