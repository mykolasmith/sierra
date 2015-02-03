import numpy as np

import time

import gevent
from gevent.event import Event

class Animation(object):
    def __init__(self, strip, controller, msg, trigger):
        self.strip = strip
        self.controller = controller
        self.msg = msg
        self.trigger = trigger
        
        self.inputs = controller.mapping.inputs_for(msg.channel, msg.note)
        self.frame = np.array([(0,0,0)] * strip.length)
        
        self.parent = gevent.getcurrent()
        self.stop = Event()
        
        if trigger == 'oneshot':
            self.accessor = id(self)
        if trigger == 'hold':
            self.accessor = msg.note
        
        self.strip.active_events[trigger][self.accessor] = self
        
    def expire(self):
        if self.accessor in self.strip.active_events[self.trigger]:
            self.strip.active_events[self.trigger].pop(self.accessor)
            
    def sleep(self, s):
        gevent.sleep(s)
        
    def spawn(self, f, *args, **kwargs):
        return gevent.spawn(f, *args, **kwargs)
    
    def worker(self, *args, **kwargs):
        raise NotImplemented
        
    def kill_parent_greenlet(self):
        gevent.kill(self.parent)
        
    def decrement(self, led, decay):
        last = tuple(self.frame[led])
        while any(self.frame[led]):
            self.frame[led] = tuple( v - decay if v - decay > 0 else v for v in self.frame[led] )
            if tuple(self.frame[led]) == last:
                self.frame[led] = (0, 0, 0)
            else:
                last = tuple(self.frame[led])
            gevent.sleep(0.)
        
class Positional(Animation):
    
    def __init__(self, strip, controller, msg):
        super(Positional, self).__init__(strip, controller, msg, 'hold')
        self.length = strip.length
        
        self.min = 36
        self.max = 59
        self.keys = self.max - self.min
        self.width = round(self.length / self.keys)
        
        self.from_pos = (self.msg.note - self.min) * self.width
        self.to_pos = self.from_pos + self.width
        self.active = xrange(int(self.from_pos), int(self.to_pos))
        r,g,b = self.controller.controls_for(msg.channel, self.inputs)
        self.spawn(self.worker, r, g, b).join()
    
    def worker(self, r, g, b):
        for i in self.active:
            self.frame[i] = (r, g, b)
            
    def off(self):
        pts = []
        for i in self.active:
            pts.append(self.spawn(self.decrement, i, 10))
        gevent.joinall(pts)
        
class MotionTween(Animation):
    
    def __init__(self, strip, controller, msg):
        # Begin an animation
        super(MotionTween, self).__init__(strip, controller, msg, 'oneshot')
        
        # Spawn + join from iterable to sequence frame workers individually
        for i in range(strip.length):
            r,g,b = self.controller.controls_for(msg.channel, self.inputs)
            self.spawn(self.worker, i, r, g, b).join()
            self.sleep(1/(1.0 * self.msg.velocity))
            
        # Always expire a oneshot when it's finished
        self.expire()
    
    def worker(self, i, r ,g ,b):
        def intensity(x):
            return (x / (self.msg.velocity / offset)) / 2.0 * x
            
        trail = list(xrange(1,5))
        for offset in trail:
            try:
                self.frame[i+offset] = map(intensity, (r,g,b))
            except IndexError:
                pass
        self.frame[i] = (0,0,0)
            
class Fade(Animation):
    
    def __init__(self, strip, controller, msg):
        super(Fade, self).__init__(strip, controller, msg, 'hold')
        self.steps = [x for x in range(127) if x % round((msg.velocity + 20) / 20) == 0 ]
        for i in self.steps:
            for led in range(self.strip.length):
                self.frame[led] = (0, 0, i)
            self.sleep(1/100.)
    
    def off(self):
        for i in reversed(self.steps):
            for led in range(self.strip.length):
                self.frame[led] = (0,0,i)
            self.sleep(1/100.)