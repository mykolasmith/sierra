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
            self.accessor = id(self)
        if trigger == 'hold':
            self.events = self.strip.holds
            self.accessor = msg.note
        
        self.events[self.accessor] = self
        self.refresh_params()
        
    def hsv_to_rgb(self, h, s, v, max=127):
        return tuple(i * 255 for i in colorsys.hsv_to_rgb(1.0/max * h, 1.0/max * s, 1.0/max * v))
        
    def get_frame(self):
        if self.controller.master:
            master = self.controller.master_for(self.msg.channel) * (1/127.0)
            return self.frame * master
        else:
            return self.frame.astype(np.int8)
            
    def refresh_params(self):
        self.params = self.controller.controls_for(self.msg.channel, self.inputs)
        
    def expire(self):
        if self.accessor in self.events:
            self.events.pop(self.accessor)
        gevent.killall(self.greenlets)
            
    def spawn(self, f, *args, **kwargs):
        g = gevent.spawn(f, *args, **kwargs)
        self.greenlets.append(g)
        return g
            
    def sleep(self, s):
        gevent.sleep(s)
        
    def decrement(self, decay=0.01):
        start = time.time()
        elapsed = 0
        counter = 0
        while self.frame.any():
            if elapsed > float(decay * counter):
                self.frame = (self.frame - 5).clip(0)
                counter += 1
            elapsed = time.time() - start
            gevent.sleep(0)
            
    def increment(self, target, attack=0.01):
        start = time.time()
        elapsed = 0
        counter = 0
        while True:
            self.refresh_params()
            state = self.hsv_to_rgb(self.params[0],127,self.params[1])
            if elapsed > float(attack * counter):
                self.frame[target] = np.array(state) * (attack * counter)
                counter += 1
            elapsed = time.time() - start
            gevent.sleep(0)
            
            
class Clear(Animation):
    
    def __init__(self,strip,controller,msg):
        super(Clear, self).__init__(strip, controller, msg, 'oneshot')
        self.strip.oneshots = {}
        self.strip.holds = {}
        
class Positional(Animation):
    
    def __init__(self, strip, controller, msg):
        super(Positional, self).__init__(strip, controller, msg, 'hold')
        
        self.min = 36
        self.max = 59
        
        self.pos = int(abs((msg.note - self.min) * (1./(self.min-self.max))) * strip.length)
        self.factor = round((5/120.) * self.strip.length)
        self.worker()
        
    def worker(self):
        while True:
            pitch = self.controller.pitchwheel_for(self.msg.channel)
            
            if self.params[2]:
                width = abs(round((pitch / 8192.) * self.factor))
                if pitch >  0:
                    leds =  xrange(self.pos, self.pos+int(width))
                if pitch <  0:
                    leds =  xrange(self.pos-int(width), self.pos+1)
                if pitch == 0:
                    leds =  [self.pos]
            else:
                width = self.factor
                leds =  xrange(self.pos, self.pos+int(width))
                
            rgb = self.hsv_to_rgb(self.params[0],127,self.params[1])
            for i in leds:
                self.frame[i] = rgb
                
            self.sleep(0) # Try commenting this out?
            
            for i in xrange(0, self.strip.length):
                self.frame[i] = (0,0,0)
            
            self.refresh_params()
            
    def off(self):
        self.decrement()
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
            if elapsed > 0.01 * counter:
                if self.params[2] == 127:
                    self.refresh_params()
                rgb = np.array(self.hsv_to_rgb(self.params[0],127,self.params[1]))
                self.worker(self.frame,counter,rgb,self.pitch,self.trail)
                counter += 1
            elapsed = time.time() - start
            gevent.sleep(0.)
    
    def worker(self,frame,i,rgb,pitch,trail):
        for offset in reversed(trail):
            factor = (1 - (float(offset) / len(trail)))
            try:
                if pitch >= 0 and i - offset > 0:
                    self.frame[i-offset] = rgb * factor
                    self.frame[i - len(trail)] = [0,0,0]
                if pitch < 0 and offset - i < 0:
                    self.frame[offset-i] = rgb * factor
                    self.frame[-i + len(trail)] = [0,0,0]
            except:
                pass
            
            
class Fade(Animation):
    
    def __init__(self, strip, controller, msg):
        super(Fade, self).__init__(strip, controller, msg, 'hold')
        rgb = self.hsv_to_rgb(self.params[0],127,self.params[1])
        
        gevent.joinall([
            self.spawn(self.increment, i) for i in xrange(0, self.strip.length)
        ])
    
    def off(self):
        self.decrement()
        self.expire()