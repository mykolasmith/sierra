from base import Animation

class Positional(Animation):
    
    def __init__(self, length, controllers, msg, notes):
        super(Positional, self).__init__(length, controllers, msg, notes, 'hold')
        
        self.min = min(notes)
        self.max = max(notes)
        
        self.params = {
            'hue': [
                0.5,
                ("ipad", "fader1"),
                ("mpk49", 4)
            ],
            'saturation' : [
                1.0,
                ("ipad", "fader2"),
                ("mpk49", 1)
            ],
            'brightness': [
                1.0,
                ("ipad", "fader3"),
                ("mpk49", 14)
            ],
            'attack' : [
                0.1,
                ("ipad", "rotary1"),
                ("mpk49", 5)
            ],
            'decay': [
                1.0,
                ("ipad", "rotary2"),
                ("mpk49", 15)
            ]
        }
        
        self.pos = int(abs((msg.note - self.min) * (1./(self.min-self.max))) * self.length)
        self.factor = round((1.0 / (self.max - self.min)) * self.length)

    def run(self, deltaMs):
        self.refresh_params()
        
        rgb = self.hsb_to_rgb(self.hue, self.saturation, self.brightness)
        factor = 1.0
        if deltaMs < self.attack:
            factor = deltaMs / self.attack
        self.pixels[self.pos:self.pos+int(self.factor)] = rgb * factor
        
    def off(self, deltaMs):
        self.fade_down(deltaMs, self.decay + 0.01)