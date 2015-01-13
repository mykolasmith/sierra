import opc
import mido
import gevent
import numpy as np
from animations import MotionTween, Fade
from gevent.queue import Queue

class Channel(object):
    
    def __init__(self, id, length):
        self.id = id
        self.length = length
        self.frame = [(0,0,0)] * length
        
        self.tasks = Queue()
        self.pending = []
        self.active_events = { 'oneshot' : {}, 'hold' : {} } 
        
        gevent.joinall([
            gevent.spawn(self.listener),
            gevent.spawn(self.scheduler),
            gevent.spawn(self.handler),
            gevent.spawn(self.aggregator),
            #gevent.spawn(self.print_events),
            gevent.spawn(self.writer),
        ])
        
        
    def handler(self):
        while True:
            if self.pending:
                gevent.joinall(self.pending)
            gevent.sleep(0.)
        
    def fire(self, msg):
        
        if msg.note == 65:
            Fade(self, msg, 'hold')
            
        if msg.note in [60, 62, 64]:
            MotionTween(self, msg, 'oneshot')
            
    def expire(self, msg):
        if msg.note in self.active_events['hold']:
            animation = self.active_events['hold'][msg.note]
            gevent.spawn(animation.off).join()
            
    def listener(self):
        bus = mido.open_input("IAC Driver Bus 1")
        print 'Connected to MIDI port: %s' % bus.name
        while True:
            for msg in bus.iter_pending():
                if msg.type == 'note_on':
                    task = { 'action' : self.fire, 'msg': msg }
                    self.tasks.put(task)
                if msg.type == 'note_off':
                    task = { 'action' : self.expire, 'msg': msg }
                    self.tasks.put(task)
            gevent.sleep(0.)

    def scheduler(self):
        while True:
            task = self.tasks.get()
            if task:
                event = gevent.spawn(task['action'], task['msg'])
                self.pending.append(event) 
            gevent.sleep(0.)
            
    def print_events(self):
        while True:
            print self.active_events
            gevent.sleep(1/10.)
            
    def aggregator(self):
        while True:
            oneshots = [ anim.frame for id, anim in
                         self.active_events['oneshot'].iteritems() ]
            holds    = [ anim.frame for id, anim in
                         self.active_events['hold'].iteritems()] 
        
            if oneshots or holds:
                self.frame = np.maximum.reduce(oneshots + holds)
            gevent.sleep(0.)

    def writer(self):
        while True:
            client.put_pixels(self.frame, self.id)
            gevent.sleep(1/60.0)
            
if __name__ == '__main__':
    client = opc.Client("beaglebone.local:7890")
    if client.can_connect():
        print 'Connected to Beaglebone...'
    
    ch = Channel(1, 120) 
