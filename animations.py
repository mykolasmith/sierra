import numpy as np

import time
import colorsys

import gevent

class Animation(object):
    
    def __init__(self, strip, controller, msg, trigger):
        self.strip = strip
        self.controller = controller
        self.msg = msg
        self.trigger = trigger
        
        self.running = False
        self.done = False
        self.t0 = None
        
        self.pixels = np.array([(0,0,0)] * strip.length, dtype=np.uint8)
        
        self.inputs = controller.mapping.inputs_for(msg.channel, msg.note)
        self.refresh_params()
        
    def hsb_to_rgb(self, h, s, v, max=127):
        # Scale hsv by max, e.g. MIDI 1-127 knob, convert to RGB, and return as numpy array
        return np.array(
            colorsys.hsv_to_rgb(
                1.0/max * h, 1.0/max * s, 1.0/max * v
            )) * 255
            
    def refresh_params(self):
        # Get current params from controller
        self.params = self.controller.controls_for(self.msg.channel, self.inputs)
        
    def fade_down(self, decay=0.01):
        # Drop the brightness of each led by 5 at a given rate of decay
        # This should probably go somewhere else...
        start = time.time()
        elapsed = 0
        counter = 0
        while self.pixels.any():
            if elapsed > float(decay * counter):
                self.pixels = (self.pixels - 5).clip(0)
                counter += 1
            elapsed = time.time() - start
        
class Positional(Animation):
    
    def __init__(self, strip, controller, msg):
        super(Positional, self).__init__(strip, controller, msg, 'hold')
        
        self.min = 36
        self.max = 59
        
        self.pos = int(abs((msg.note - self.min) * (1./(self.min-self.max))) * strip.length)
        self.factor = round((5/120.) * self.strip.length)

    def run(self, deltaMs):
        #hue = self.params[0]
        hue = 64
        if self.params[2]:
            color = self.controller.globals.get('color', 64)
            if color > 64:
                saturation = (color - 64) * 2
            else:
                saturation = color * 2
        else:
            saturation = 127
        #brightness = self.params[1]
        brightness = 127
        rgb = self.hsb_to_rgb(hue, saturation, brightness)
        self.pixels[self.pos:self.pos+int(self.factor)] = rgb
        
class MotionTween(Animation):
    
    def __init__(self, strip, controller, msg):
        super(MotionTween, self).__init__(strip, controller, msg, 'oneshot')
        self.trail = xrange(0,5)
        self.pitch = controller.pitchwheel_for(msg.channel)
            
        if self.pitch != 0:
            self.trail = xrange(0, int((abs(self.pitch) / 409.6)))
        
        self.num_frames = self.strip.length + len(self.trail)
        self.refresh_enabled = self.params[2]
        self.djm_enabled = self.params[4]
        #speed = self.params[3]
        self.duration = 2.0
        
    def run(self, deltaMs):
        frame = int(self.num_frames * (deltaMs / self.duration))
        if frame > self.num_frames:
            self.done = True
            
        if self.refresh_enabled:
            self.refresh_params()
            
        #hue = self.params[0]
        hue = 64
        
        if self.djm_enabled:
            color = self.controller.globals.get('color', 64)
            if color > 64:
                saturation = (127 - color) * 2
            else:
                saturation = color * 2
        else:
            saturation = 127
            
        #brightness = self.params[1]
        brightness = 127
        
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
