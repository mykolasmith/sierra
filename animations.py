import numpy as np

import time
import math
import colorsys

import gevent

class Animation(object):
    
    def __init__(self, strip, controllers, msg, trigger):
        self.strip = strip
        self.controllers = controllers
        self.controllers.via_channel(msg.channel + 1)
        self.msg = msg
        self.trigger = trigger
        
        self.running = False
        self.done = False
        
        self.pixels = np.array([(0,0,0)] * strip.length, dtype=np.uint8)
        
    def run(self, deltaMs):
        pass
        
    def off(self, deltaMs):
        pass
        
    def hsb_to_rgb(self, h, s, v, max=127):
        # Scale hsv by max, e.g. MIDI 1-127 knob, convert to RGB, and return as numpy array
        return np.array(
            colorsys.hsv_to_rgb(
                1.0/max * h, 1.0/max * s, 1.0/max * v
            )) * 255
            
    def fade_down(self, deltaMs, decay=1.0):
        if deltaMs > decay or not self.pixels.any():
            self.done = True
        else:
            factor = 1 - (deltaMs / decay)
            self.pixels = (self.pixels * factor).astype(np.uint8)
        
class Positional(Animation):
    
    def __init__(self, strip, controllers, msg):
        super(Positional, self).__init__(strip, controllers, msg, 'hold')
        
        self.min = 36
        self.max = 59
        
        self.decay = 5.0
        self.pos = int(abs((msg.note - self.min) * (1./(self.min-self.max))) * strip.length)
        self.factor = round((5/120.) * self.strip.length)

    def run(self, deltaMs):
        hue = self.controllers.get("mpk49", "F1", 64)
        saturation = self.controllers.get("nexus", "color", 127)
        brightness = self.controllers.get("mpk49", "master", 127)
        
        rgb = self.hsb_to_rgb(hue, saturation, brightness)
        self.pixels[self.pos:self.pos+int(self.factor)] = rgb
        
    def off(self, deltaMs):
        self.fade_down(deltaMs, decay=self.decay)
        
class Rainbow(Animation):
    
    def __init__(self,strip,controllers,msg):
        super(Rainbow, self).__init__(strip, controllers, msg, 'toggle')
        self.decay = 5.0
    
    def run(self, deltaMs):
        for led in range(self.strip.length):
            r = math.sin(led * .2 + (deltaMs * 5)) * 127 + 128
            g = math.sin(led * .2 + (deltaMs * 5) + 2) * 127 + 128
            b = math.sin(led * .2 + (deltaMs * 5) + 4) * 127 + 128
            self.pixels[-led] = [r,g,b]
        
    def off(self, deltaMs):
        self.fade_down(deltaMs, decay=self.decay)

class MotionTween(Animation):
    
    def __init__(self, strip, controllers, msg):
        super(MotionTween, self).__init__(strip, controllers, msg, 'oneshot')
        self.trail = xrange(0,5)
        self.pitch = 0
            
        if self.pitch != 0:
            self.trail = xrange(0, int((abs(self.pitch) / 409.6)))
        
        self.num_frames = self.strip.length + len(self.trail)
        #self.refresh_enabled = self.params[2]
        #self.djm_enabled = self.params[4]
        #speed = self.params[3]
        self.duration = 2.0
        
    def run(self, deltaMs):
        frame = int(self.num_frames * (deltaMs / self.duration))
        if frame >= self.num_frames:
            self.done = True
            return
            
        #if self.refresh_enabled:
        #    self.refresh_params()
            
        #hue = self.params[0]
        hue = self.controllers.get("mpk49", "F1", 64)
        saturation = self.controllers.get("mpk49", "S1", 127)
        brightness = self.controllers.get("mpk49", "K1", 127)
        
        #if self.djm_enabled:
        #    color = self.controller.globals.get('color', 64)
        #    if color > 64:
        #        saturation = (127 - color) * 2
        #    else:
        #        saturation = color * 2
        #else:
        #    saturation = 127
        
        rgb = self.hsb_to_rgb(hue,saturation,brightness)
        for offset in reversed(self.trail):
            factor = (1 - (float(offset) / len(self.trail)))
            try:
                if self.pitch >= 0 and frame - offset > 0:
                    self.pixels[frame-offset] = rgb * factor
                    self.pixels[frame - len(self.trail)] = [0,0,0]
                if self.pitch < 0 and offset - i < 0:
                    self.pixels[offset-frame] = rgb * factor
                    self.pixels[-frame + len(self.trail)] = [0,0,0]
            except:
                pass
