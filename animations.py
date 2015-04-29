import numpy as np

import time
import math
import colorsys

import gevent

class Animation(object):
    
    def __init__(self, length, controllers, msg, notes, trigger):
        self.length = length
        
        self.controllers = controllers
        self.controllers.via_channel(msg.channel)
        
        self.msg = msg
        self.notes = notes
        self.trigger = trigger
        
        self.running = False
        self.done = False
        
        self.pixels = np.array([(0,0,0)] * length, dtype=np.uint8)
        
    def run(self, deltaMs):
        pass
        
    def off(self, deltaMs):
        pass
        
    def normalize(self, val, prev_min, prev_max, new_min, new_max):
        if val == prev_min:
            return new_min
        elif val == prev_max:
            return new_max
        else:
            return (float(val) / (prev_max - prev_min)) * (new_max - new_min)
        
    def hsb_to_rgb(self, h, s, v, max=127):
        # Scale hsv by max, e.g. MIDI 1-127 knob, convert to RGB, and return as numpy array
        return np.array(
            colorsys.hsv_to_rgb(
                1.0/max * h, 1.0/max * s, 1.0/max * v
            )) * 255
            
    def fade_down(self, deltaMs, decay):
        if deltaMs > decay:
            self.done = True
        else:
            factor = 1.0 - (deltaMs / decay)
            self.pixels = self.pixels_at_inflection * factor
            
class Fidget(Animation):
    
    def __init__(self, strip, controllers, msg, notes):
        super(Fidget, self).__init__(strip, controllers, msg, notes, 'hold')
        
class Positional(Animation):
    
    def __init__(self, strip, controllers, msg, notes):
        super(Positional, self).__init__(strip, controllers, msg, notes, 'hold')
        
        self.min = min(notes)
        self.max = max(notes)
        
        self.decay = 1.0
        self.pos = int(abs((msg.note - self.min) * (1./(self.min-self.max))) * self.length)
        self.factor = round((1.0 / (self.max - self.min)) * self.length)

    def run(self, deltaMs):
        hue = self.controllers.get("mpk49", "F1", 64)
        saturation = self.controllers.get("nexus", "color", 127)
        brightness = self.controllers.get("mpk49", "master", 127)
        
        rgb = self.hsb_to_rgb(hue, saturation, brightness)
        self.pixels[self.pos:self.pos+int(self.factor)] = rgb
        
    def off(self, deltaMs):
        self.fade_down(deltaMs, self.decay)
        
class Rainbow(Animation):
    
    def __init__(self, length, controllers, msg, notes):
        super(Rainbow, self).__init__(length, controllers, msg, notes, 'toggle')
        self.decay = 1.0
    
    def run(self, deltaMs):
        x = self.controllers.get("mpk49", "F1", 127)
        speed = self.normalize(x, 0, 127, -0.2, -8.9)
        for i in xrange(0, self.length):
            r=math.sin(i * .2+ deltaMs * speed ) * 127 + 128
            g=math.sin(i * .2+ deltaMs * speed + 2 ) * 127 + 128
            b=math.sin(i * .2+ deltaMs * speed + 4 ) * 127 + 128
            self.pixels[i] = [r,g,b]
        
    def off(self, deltaMs):
        self.fade_down(deltaMs, self.decay)

class MotionTween(Animation):
    
    def __init__(self, strip, controllers, msg, notes):
        super(MotionTween, self).__init__(strip, controllers, msg, notes, 'oneshot')
        self.trail = xrange(0,5)
        self.pitch = 0
            
        if self.pitch != 0:
            self.trail = xrange(0, int((abs(self.pitch) / 409.6)))
        
        self.num_frames = self.length + len(self.trail)
        self.duration = 2.0
        
        self.refresh_enabled = self.controllers.get("mpk49", "F2", 0)
        self.djm_enabled = self.controllers.get("mpk49", "F3", 0)
        
        self.refresh_params()
        
    def refresh_params(self):
        self.hue = self.controllers.get("mpk49", "F1", 64)
        self.saturation = 127
        self.brightness = 127
        
    def run(self, deltaMs):
        frame = round(self.num_frames * (deltaMs / self.duration))
        if frame >= self.num_frames:
            self.done = True
            return
            
        if self.refresh_enabled:
            self.refresh_params()
        
        if self.djm_enabled:
            color = self.controllers.get('color', 64)
        
        rgb = self.hsb_to_rgb(self.hue,self.saturation,self.brightness)
        for offset in reversed(self.trail):
            factor = 1 - (float(offset) / len(self.trail))
            try:
                if self.pitch >= 0 and frame - offset > 0:
                    self.pixels[frame-offset] = rgb * factor
                    self.pixels[frame - len(self.trail)] = [0,0,0]
                if self.pitch < 0 and offset - i < 0:
                    self.pixels[offset-frame] = rgb * factor
                    self.pixels[-frame + len(self.trail)] = [0,0,0]
            except IndexError:
                pass
