from base import Animation
import noise
import math

class Perlin(Animation):
    
    def __init__(self, config):
        super(Perlin, self).__init__(config, 'toggle')
        
        self.scale = 0.01
        self.speed = 0.5
        self.octave = 1
        self.mmax = 0.0001
        self.mmin = 0.0001
        self.decay = 0.25
        self.z = 0
        
        self.refresh_params()
        
    def run(self, deltaMs):

        for x in range(self.length):
            c = noise.pnoise3(x * self.scale, self.scale, self.z * self.scale, self.octave)
            
            if c > self.mmax: self.mmax = c
            if c < self.mmin: self.mmin = c
    
            c = c + math.fabs(self.mmin)
            c = c / (self.mmax + math.fabs(self.mmin))
            
            c = (c + 0.2) % 1
            self.pixels[x] = self.hsb_to_rgb(c,self.saturation,self.brightness)
         
        # Speed of the animation
        self.z += self.speed
        
    def off(self, deltaMs):
        self.refresh_params()
        if deltaMs >= self.decay:
            self.pixels[...] = 0
            self.done = True
        else:
            factor = 1.0 - (deltaMs / self.decay)
            self.pixels = self.pixels_at_inflection * factor