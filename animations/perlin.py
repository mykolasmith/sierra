from base import Animation
import noise
import math

class Perlin(Animation):
    
    def __init__(self, length, controllers, msg, notes):
        super(Perlin, self).__init__(length, controllers, msg, notes, 'toggle')
        self.z = 0
        
        # Distance between blocks? 0.75 = very narrow, 0.01 = very wide
        self.scale = 0.05

        self.octave = 1
        self.mmax = 0.0001
        self.mmin = 0.0001
        self.decay = 0.25
        
    def run(self, deltaMs):
        
        for x in range(self.length):
            c = noise.pnoise3(x * self.scale, self.scale, self.z * self.scale, self.octave)

            if c > self.mmax: self.mmax = c
            if c < self.mmin: self.mmin = c
    
            c = c + math.fabs(self.mmin)
            c = c / (self.mmax + math.fabs(self.mmin))
            
            #TODO: What does 0.2 coefficient do?
            c = (c + 0.2) % 1
            self.pixels[x] = self.hsb_to_rgb(c,1,1,max=1)
         
        # Speed of the animation
        self.z += 0.1
        
    def off(self, deltaMs):
        self.fade_down(deltaMs, self.decay)