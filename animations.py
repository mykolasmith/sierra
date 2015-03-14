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
        
        self.frame = np.array([(0,0,0)] * strip.length)
        
        # Different types of triggers have different behavior with respect to strip's active events
        if trigger == 'oneshot':
            # For oneshots, each animation is unique and show be removed after the whole thing has completed
            self.events = self.strip.oneshots
            self.accessor = id(self)
        if trigger == 'hold':
            # For holds, the note_on/note_off message determines whether the animation is active or not
            self.events = self.strip.holds
            self.accessor = msg.note
        
        # Start an animation by adding it to the strip's active events
        self.events[self.accessor] = self
        
        self.inputs = controller.mapping.inputs_for(msg.channel, msg.note)
        self.refresh_params()
        
    def hsv_to_rgb(self, h, s, v, max=127):
        # Scale hsv by max, e.g. MIDI 1-127 knob, conver to RGB, and return as numpy array
        return np.array(colorsys.hsv_to_rgb(1.0/max * h, 1.0/max * s, 1.0/max * v)) * 255
        
    def get_frame(self):
        # Apply the master, if we're using it with this controller mapping
        if self.controller.master:
            master = self.controller.master_for(self.msg.channel) * (1/127.0)
            return self.frame * master
        else:
            return self.frame
            
    def refresh_params(self):
        # Get current params from controller
        self.params = self.controller.controls_for(self.msg.channel, self.inputs)
        
    def clear(self):
        # Clear the strip
        self.frame = np.zeros_like(self.frame)
        
    def expire(self):
        # The animation is done. Clear the strip and remove this animation from the strip's active events.
        self.clear()
        if self.accessor in self.events:
            self.events.pop(self.accessor)
        self.done = True
        
    def fade_down(self, decay=0.01):
        # Drop the brightness of each led by 5 at a given rate of decay
        # This should probably go somewhere else...
        start = time.time()
        elapsed = 0
        counter = 0
        while self.frame.any():
            if elapsed > float(decay * counter):
                self.frame = (self.frame - 5).clip(0)
                counter += 1
            elapsed = time.time() - start
            gevent.sleep(0)
        self.expire()
        
class Clear(Animation):
    
    def __init__(self,strip,controller,msg):
        super(Clear, self).__init__(strip, controller, msg, 'oneshot')
        self.clear()
        strip.oneshots = {}
        strip.holds = {}
        
class Positional(Animation):
    
    def __init__(self, strip, controller, msg):
        super(Positional, self).__init__(strip, controller, msg, 'hold')
        
        self.min = 36
        self.max = 59
        
        self.pos = int(abs((msg.note - self.min) * (1./(self.min-self.max))) * strip.length)
        self.factor = round((5/120.) * self.strip.length)

        hue = self.params[0]
        if self.params[2]:
            color = self.controller.globals.get('color', 64)
            if color > 64:
                saturation = (color - 64) * 2
            else:
                saturation = color * 2
        else:
            saturation = 127
        value = self.params[1]
        rgb = self.hsv_to_rgb(hue, saturation, value)
        self.frame[self.pos:self.pos+int(self.factor)] = rgb
            
    def off(self):
        self.fade_down()
        self.expire()
        
class MotionTween(Animation):
    
    def __init__(self, strip, controller, msg):
        super(MotionTween, self).__init__(strip, controller, msg, 'oneshot')
        self.trail = xrange(0,5)
        self.pitch = controller.pitchwheel_for(msg.channel)
            
        if self.pitch != 0:
            self.trail = xrange(0, int((abs(self.pitch) / 409.6)))
        
        num_frames = self.strip.length + len(self.trail)
        self.animator(num_frames, self.params[4])
        
    def animator(self, num_frames, speed):
        start = time.time()
        counter = 0
        elapsed = 0
        while num_frames - counter >= 0:
            if elapsed > 0.01 * (speed/127. * 1.5) * counter:
                if self.params[2]:
                    self.refresh_params()
                hue = self.params[0]
                if self.params[3]:
                    color = self.controller.globals.get('color', 64)
                    if color > 64:
                        saturation = (127 - color) * 2
                    else:
                        saturation = color * 2
                else:
                    saturation = 127
                value = self.params[1]
                rgb = self.hsv_to_rgb(hue,saturation,value)
                self.worker(self.frame,counter,rgb,self.pitch,self.trail)
                counter += 1
            elapsed = time.time() - start
            gevent.sleep(0)
        self.expire()
    
    def worker(self,frame,i,rgb,pitch,trail):
        for offset in reversed(trail):
            factor = (1 - (float(offset) / len(trail)))
            try:
                if pitch >= 0 and i - offset > 0:
                    frame[i-offset] = rgb * factor
                    frame[i - len(trail)] = [0,0,0]
                if pitch < 0 and offset - i < 0:
                    frame[offset-i] = rgb * factor
                    frame[-i + len(trail)] = [0,0,0]
            except:
                pass