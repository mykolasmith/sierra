from base import Animation
import noise
import math

class Perlin(Animation):
    
    def __init__(self, length, controllers, msg, notes):
        super(Perlin, self).__init__(length, controllers, msg, notes, 'toggle')
        
        self.scale = 0.01
        self.speed = 0.5
        self.octave = 1
        self.mmax = 0.0001
        self.mmin = 0.0001
        self.decay = 0.25
        self.z = 0
        
        self.params = {
            'saturation' : [
                1.0,
                ("midi", 1)
            ],
            'min_hue' : [
                0,
                ("osc", "rotary3"),
                ("midi", 17)
            ],
            'max_hue' : [
                1.0,
                ("osc", "rotary4"),
                ("midi", 18)
            ],
            'brightness' : [
                1,
                ("osc", "rotary5"),
                ("midi", 8)
            ]
        }
        
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