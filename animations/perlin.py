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
        
        self.params = {
            'saturation' : [
                1.0,
                ("mpk49", 1)
            ],
            'min_hue' : [
                0,
                ("ipad", "rotary3"),
                ("mpk49", 17)
            ],
            'max_hue' : [
                1.0,
                ("ipad", "rotary4"),
                ("mpk49", 18)
            ],
            'scale' : [
                0.05,
                ("mpk49", 9)
            ],
            'speed' : [
                0.1,
                ("ipad", "fader4"),
                ("mpk49", 19)
            ],
            'brightness' : [
                1,
                ("ipad", "rotary5"),
                ("mpk49", 8)
            ]
        }
        
    def run(self, deltaMs):
        self.refresh_params()
        
        self.speed = self.normalize(self.speed, 0., 1., 0., 0.5)
        self.scale = self.normalize(self.scale + 0.01, 0.01, 1.0, 0.01, 0.25)
        
        for x in range(self.length):
            c = noise.pnoise3(x * self.scale, self.scale, self.z * self.scale, self.octave)

            if c > self.mmax: self.mmax = c
            if c < self.mmin: self.mmin = c
    
            c = c + math.fabs(self.mmin)
            c = c / (self.mmax + math.fabs(self.mmin))
            
            #TODO: What does 0.2 coefficient do?
            c = (c + 0.2) % 1
            if c >= self.min_hue and c <= self.max_hue:
                self.pixels[x] = self.hsb_to_rgb(c,self.saturation,self.brightness)
         
        # Speed of the animation
        self.z += self.speed + 0.01
        
    def off(self, deltaMs):
        self.fade_down(deltaMs, self.decay)