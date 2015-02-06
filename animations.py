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
        
        self.parent = gevent.getcurrent()
        self.inputs = controller.mapping.inputs_for(msg.channel, msg.note)
        self.frame = np.array([(0,0,0)] * strip.length)
        
        if trigger == 'oneshot':
            self.events = self.strip.oneshots
            self.accessor = id(self)
        if trigger == 'hold':
            self.events = self.strip.holds
            self.accessor = msg.note
        
        self.events[self.accessor] = self
        
    def get_frame(self):
        if self.controller.master:
            master = self.controller.master_for(self.msg.channel) * (1/127.0)
            return self.frame * master
        else:
            return self.frame
        
    def expire(self):
        if self.accessor in self.events:
            self.events.pop(self.accessor)
            
    def spawn(self, f, *args, **kwargs):
        return gevent.spawn(f, *args, **kwargs)
            
    def sleep(self, s):
        gevent.sleep(s)
        
    def decrement(self, decay):
        while self.frame.any():
            self.frame = (self.frame - decay).clip(0)
            gevent.sleep(1/70.)

class Positional(Animation):
    
    def __init__(self, strip, controller, msg):
        super(Positional, self).__init__(strip, controller, msg, 'hold')
        
        self.min = 36
        self.max = 59
        #TODO fix this
        
        self.keys = self.max - self.min
        self.width = round(self.strip.length / self.keys)
        
        self.from_pos = (self.msg.note - self.min) * self.width
        self.to_pos = self.from_pos + self.width
        self.active = xrange(int(self.from_pos), int(self.to_pos))
        r,g,b = self.controller.controls_for(msg.channel, self.inputs)
        
        self.spawn(self.worker, r, g, b).join()
    
    def worker(self, r, g, b):
        for i in self.active:
            self.frame[i] = (r, g, b)
            
    def off(self):
        self.spawn(self.decrement, 10).join()
        
class MotionTween(Animation):
    
    def __init__(self, strip, controller, msg):
        # Begin an animation
        super(MotionTween, self).__init__(strip, controller, msg, 'oneshot')
        self.steps = xrange(0, strip.length) 
        self.trail = xrange(0,5) #TODO Is it faster to make it self.trail and call from within the worker, or pass it in?

        if controller.pitchwheel:
            self.pitch = controller.pitchwheel_for(msg.channel)
            
            if self.pitch != 0:
                self.trail = xrange(0, int((abs(self.pitch) / 409.6)))
        
        r,g,b = self.controller.controls_for(msg.channel, self.inputs)

        for i in self.steps:
            self.spawn(self.worker, i, r, g, b).join()
            self.sleep(1/(1.0 * self.msg.velocity))
            
        # Always expire a oneshot when it's finished
        self.expire()
    
    def worker(self, i, r ,g ,b):
        
        def intensity(v):
            return (2 * v) * (127 / 127.0) * (1 - (float(offset) / len(self.trail)))
            
        for offset in reversed(self.trail):
            if self.pitch >= 0 and i - offset > 0:
                self.frame[i - offset] =  map(intensity, (r,g,b))
                self.frame[i - len(self.trail)] = (0,0,0)
            if self.pitch < 0 and -i + offset < 0:
                self.frame[offset - i] = map(intensity, (r,g,b))
                self.frame[-i + len(self.trail)] = (0,0,0)
            
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