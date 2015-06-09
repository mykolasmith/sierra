from base import Animation

class Positional(Animation):
    
    def __init__(self, length, controllers, msg, notes):
        super(Positional, self).__init__(length, controllers, msg, notes, 'hold')
        
        self.min = min(notes)
        self.max = max(notes)
        
        self.params = {
            'hue': [
                0.5,
                ("mpk49", 12)
            ],
            'saturation': [
                1.0,
                ("nexus", "color")
            ],
            'brightness': [
                1.0,
                ("mpk49", 14)
            ],
            'decay': [
                1.0,
                ("mpk49", None)
            ]
        }
        
        self.pos = int(abs((msg.note - self.min) * (1./(self.min-self.max))) * self.length)
        self.factor = round((1.0 / (self.max - self.min)) * self.length)

    def run(self, deltaMs):
        self.refresh_params()
        
        rgb = self.hsb_to_rgb(self.hue, self.saturation, self.brightness)
        self.pixels[self.pos:self.pos+int(self.factor)] = rgb
        
    def off(self, deltaMs):
        self.fade_down(deltaMs, self.decay)