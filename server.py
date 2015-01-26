import opc
import gevent
from gevent.queue import Queue

from input import MidiController
from mapping import Mapping
from strip import Strip

from animations import MotionTween, Fade
        
class Universe(object):
    
    def __init__(self, client, strips, controllers, mapping):
        print 'Starting Universe...'
        self.client = client
        self.strips = strips
        self.mapping = mapping
        self.controllers = controllers
        
        self.tasks = Queue()
        self.pending = []
        
        gevent.joinall([
            gevent.spawn(self.start),
            #gevent.spawn(self.debug),
            gevent.spawn(self.scheduler),
            gevent.spawn(self.handler),
            gevent.spawn(self.writer)
        ])
        
    def start(self):
        gevent.joinall(
            [ gevent.spawn(controller.listener, self) for controller in self.controllers.itervalues()] +
            [ gevent.spawn(strip.aggregator, self) for strip in self.strips.itervalues() ]
        )
        
    def debug(self):
        while True:
            print(chr(27) + "[2J")
            print 'EVENTS'
            print '------'
            print '\n'
            for strip in self.strips.itervalues():
                print strip, strip.active_events
            print '\n'
            print 'MAPPINGS'
            print '--------'
            print '\n'
            print self.mapping.animations
            print self.mapping.inputs
            print self.mapping.strips
            gevent.sleep(1/3.)
        
    def scheduler(self): 
        while True:
            while not self.tasks.empty():
                task = self.tasks.get(timeout=0)
                event = gevent.spawn(
                    task['animation'],
                    task['strip'],
                    task['controller'],
                    task['msg']
                )
                self.pending.append(event)
            gevent.sleep(0.)
    
    def handler(self):
        while True:
            if self.pending:
                gevent.joinall(self.pending)
                self.pending = []
            gevent.sleep(0.)
        
    def writer(self):
        while True:
            for channel, strip in strips.iteritems():
                self.client.put_pixels(strip.frame, channel)
            gevent.sleep(1/500.)
            
if __name__ == '__main__':
    connected = False
    client = opc.Client("beaglebone.local:7890")
    
    if client.can_connect():
        connected = True
        print 'Connected to Beaglebone...'

    strips = {
        1: Strip(120),
        2: Strip(300)
    }
    
    group_1 = [strips.get(1), strips.get(2)]
    
    controllers = {
        'mpk49' : MidiController("IAC Driver Bus 1")
    }
    
    mapping = Mapping(controllers['mpk49'])
    mapping.add(strips=[strips.get(1)],
                channel=1,
                note=60,
                animation=MotionTween,
                inputs=[12,13,14])
    mapping.add(strips=[strips.get(2)],
                channel=1,
                note=62,
                animation=MotionTween,
                inputs=[12,13,14])
    mapping.add(strips=group_1,
                channel=1,
                note=64,
                animation=Fade)
    
    universe = Universe(client, strips, controllers,  mapping)
