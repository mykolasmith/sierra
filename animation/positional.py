from base import Animation

import math

class Positional(Animation):
    
    def __init__(self, config):
        super(Positional, self).__init__(config, 'hold')
        
        # Look at the range of notes assigned to this animations
        # In order to determine the min and max
        self.min = min(self.notes)
        self.max = max(self.notes)
        
        # The min and max can then be used to deterine the correct
        # position for a set of LEDs, depending on the note pressed.
        
        self.width = (1. / (self.max - self.min)) * self.length
        self.start = int(msg.note * self.width)
        self.end = int(round(self.start + self.width))
        self.midpoint = self.start + (self.width // 2)
        self.last = self.width

    def run(self, deltaMs):
        width = self.find_width(deltaMs)
        if width == 1.0 or self.speed == 0.0:
            self.refresh_params()
        
        if deltaMs < self.attack:
            self.brightness = deltaMs / self.attack
        else:
            self.brightness = 1.0
        
        self.draw(width)
        
    def off(self, deltaMs):
        if deltaMs >= self.decay:
            self.pixels[...] = 0
            self.done = True
        else:
            self.brightness = 1 - (deltaMs / self.decay)
            width = self.find_width(deltaMs)
            self.draw(width)
            
    def find_width(self, deltaMs):
        if self.speed != 0:
            speed = self.normalize(self.speed, 0, 10)
            return round(self.width * abs(math.sin(deltaMs * speed)))
        return self.width
            
    def draw(self, width):
        
        rgb = self.hsb_to_rgb(self.hue, self.saturation, self.brightness)
        self.pixels[self.midpoint] = rgb
        for px in reversed(xrange(1, int(round(width // 2)))):
            factor = 1- (px / (width // 2))
            self.pixels[self.midpoint+px] = rgb * factor
            self.pixels[self.midpoint-px] = rgb * factor