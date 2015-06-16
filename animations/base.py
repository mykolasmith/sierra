import numpy as np
import colorsys
import math

class Animation(object):
    
    def __init__(self, length, controllers, msg, notes, trigger):
        self.length = length
        
        self.controllers = controllers
        self.msg = msg
        self.notes = notes
        self.trigger = trigger
        
        self.running = False
        self.done = False
        
        self.pixels = np.array([(0,0,0)] * length, dtype=np.uint8)
        
    def run(self, deltaMs):
        pass
        
    def off(self, deltaMs):
        self.pixels[...] = 0
        
    def normalize(self, val, prev_min, prev_max, new_min, new_max):
        if val == prev_min:
            return new_min
        elif val == prev_max:
            return new_max
        else:
            return (float(val) / (prev_max - prev_min)) * (new_max - new_min)
            
    def refresh_params(self):
        params = self.controllers.parse_params(self.msg.channel, self.params)
        for param, val in params.iteritems():
            setattr(self, param, val)
        
    def hsb_to_rgb(self, h, s, b):
        # Scale hsv by max, e.g. MIDI 1-127 knob, convert to RGB, and return as numpy array
        return np.array(colorsys.hsv_to_rgb(h, s, b)) * 255
            
    def fade_down(self, deltaMs, decay):
        if deltaMs > decay:
            self.done = True
            self.pixels[...] = 0
        else:
            factor = 1.0 - (deltaMs / decay)
            self.pixels = self.pixels_at_inflection * factor
