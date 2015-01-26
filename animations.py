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
        
        self.inputs = controller.universe.mapping.inputs[msg.channel][msg.note]
        self.frame = np.array([(0,0,0)] * strip.length)
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
        
    def off(self):
        raise NotImplemented
        
class MotionTween(Animation):
    
    def __init__(self, strip, controller, msg):
        # Begin an animation
        super(MotionTween, self).__init__(strip, controller, msg, 'oneshot')
        
        # Spawn + join from iterable to sequence individually
        for i in range(strip.length):
            r,g,b = self.controller.controls_for(msg.channel, self.inputs)
            self.spawn(self.worker, i, r, g, b).join()
            self.sleep(1/(1.0 * self.msg.velocity))
            
        # Expire the event when you're finished
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
        self.spawn(self.worker, self.steps).join()
    
    def off(self):
        self.stop.set()
        self.set_pixels(0)
        
    def set_pixels(self, i):
        for led in range(self.strip.length):
            self.frame[led] = (0, 0, i)
        self.sleep(1/100.)
    
    def worker(self, steps):
        for i in steps:
            if not self.stop.isSet():
                self.set_pixels(i)
                