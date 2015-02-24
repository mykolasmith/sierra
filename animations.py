import numpy as np

import time
import colorsys

import gevent
from gevent.event import Event

class Animation(object):
    def __init__(self, strip, controller, msg, trigger):
        self.strip = strip
        self.controller = controller
        self.msg = msg
        self.trigger = trigger
        
        self.greenlets = [ gevent.getcurrent() ]
        self.inputs = controller.mapping.inputs_for(msg.channel, msg.note)
        self.frame = np.array([(0,0,0)] * strip.length)
        
        if trigger == 'oneshot':
            self.events = self.strip.oneshots
            self.events.append(self)
            self.remove = lambda: self.events.remove(self)
        if trigger == 'hold':
            self.events = self.strip.holds
            self.accessor = msg.note
            self.events[self.accessor] = self
            self.remove = lambda: self.events.pop(self.accessor)
        
        self.refresh_params()
        
    def hsv_to_rgb(self, h, s, v, max=127):
        return tuple(i * 255 for i in colorsys.hsv_to_rgb(1.0/max * h, 1.0/max * s, 1.0/max * v))
        
    def get_frame(self):
        if self.controller.master:
            master = self.controller.master_for(self.msg.channel) * (1/127.0)
            return self.frame * master
        else:
            return self.frame
            
    def refresh_params(self):
        self.params = self.controller.controls_for(self.msg.channel, self.inputs)
        
    def expire(self):
        self.remove()
        gevent.killall(self.greenlets)
            
    def spawn(self, f, *args, **kwargs):
        g = gevent.spawn(f, *args, **kwargs)
        self.greenlets.append(g)
        return g
            
    def sleep(self, s):
        gevent.sleep(s)
        
    def decrement(self, decay):
        while self.frame.any():
            self.frame = (self.frame - 5).clip(0)
            gevent.sleep(1. / decay)
            
    def increment(self, target, state, attack):
        while not np.array_equal(self.frame[target], state):
            for k,v in enumerate(self.frame[target]):
                if v < state[k]:
                    self.frame[target][k] += 5
                else:
                    self.frame[target][k] = state
            gevent.sleep(1. / attack)
            
class Clear(Animation):
    
    def __init__(self,strip,controller,msg):
        super(Clear, self).__init__(strip, controller, msg, 'oneshot')
        self.strip.oneshots = []
        self.strip.holds = {}
        
class Positional(Animation):
    
    def __init__(self, strip, controller, msg):
        super(Positional, self).__init__(strip, controller, msg, 'hold')
        
        self.min = 36
        self.max = 59
        
        self.pos = int(abs((msg.note - self.min) * (1./(self.min-self.max))) * strip.length)
        self.h, self.v, self.toggle = self.params
        self.spawn(self.worker).join()
        
    def worker(self):
        while True:
            t0 = time.time()
            pitch = self.controller.pitchwheel_for(self.msg.channel)
            
            factor =  round((5/120.) * self.strip.length)
            
            if self.toggle:
                width = abs(round((pitch / 8192.) * factor))
                if pitch > 0:
                    leds = xrange(self.pos, self.pos+int(width))
                if pitch < 0:
                    leds = xrange(self.pos-int(width), self.pos+1)
                if pitch == 0:
                    leds = [self.pos]
            else:
                width = factor
                leds = xrange(self.pos, self.pos+int(width))
                
            rgb = self.hsv_to_rgb(self.h,127,self.v)
            for i in leds:
                self.frame[i] = rgb
                
            self.sleep(time.time()- t0) # Try commenting this out?
            
            for i in xrange(0, self.strip.length):
                self.frame[i] = (0,0,0)
            
    def off(self):
        self.decrement(100)
        self.expire()
        
class MotionTween(Animation):
    
    def __init__(self, strip, controller, msg):
        super(MotionTween, self).__init__(strip, controller, msg, 'oneshot')
        self.trail = xrange(0,5)

        if controller.pitchwheel:
            self.pitch = controller.pitchwheel_for(msg.channel)
            
            if self.pitch != 0:
                self.trail = xrange(0, int((abs(self.pitch) / 409.6)))
        
        num_frames = self.strip.length + len(self.trail)
        self.animator(num_frames)
        self.expire()
        
    def animator(self, num_frames):
        start = time.time()
        counter = 0
        elapsed = 0
        while num_frames - counter >= 0:
            t0 = time.time()
            if elapsed > 0.01 * counter:
                if self.params[2] == 127:
                    self.refresh_params()
                self.worker(counter,self.params[0],127,self.params[1])
                counter += 1
            elapsed = time.time() - start
            gevent.sleep(0)
            
    def worker(self,i,h,s,v):
        
        def intensity(x):
            return x * (1 - (float(offset) / len(self.trail)))
            
        for offset in reversed(self.trail):
            try:
                if self.pitch >= 0 and i - offset > 0:
                    self.frame[i - offset] =  map(intensity, self.hsv_to_rgb(h,s,v))
                    self.frame[i - len(self.trail)] = (0,0,0)
                if self.pitch < 0 and -i + offset < 0:
                    self.frame[offset - i] = map(intensity, self.hsv_to_rgb(h,s,v))
                    self.frame[-i + len(self.trail)] = (0,0,0)
            except:
                pass
            
class Fade(Animation):
    
    # TODO: This is a big fat work in progress
    
    def __init__(self, strip, controller, msg):
        super(Fade, self).__init__(strip, controller, msg, 'hold')
        self.h, self.v = self.controller.controls_for(msg.channel, self.inputs)
        self.spawn(self.worker).join()
        
    def worker(self):
        rgb = self.hsv_to_rgb(self.h, 127, self.v)
        for led in range(self.strip.length):
            self.frame[led] = rgb
    
    def off(self):
        self.spawn(self.decrement, 1.0).join()
        self.expire()