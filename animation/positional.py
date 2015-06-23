from base import Animation

class Positional(Animation):
    
    def __init__(self, length, controllers, msg, notes):
        super(Positional, self).__init__(length, controllers, msg, notes, 'hold')
        
        # Look at the range of notes assigned to this animations
        # In order to determine the min and max
        self.min = min(notes)
        self.max = max(notes)
        
        self.params = {
            'hue': [
                0.5,
                ("midi", 1)
            ],
            'saturation' : [
                1.0,
                ("osc", "fader2"),
            ],
            'brightness': [
                1.0,
                ("osc", "fader3"),
            ],
            'attack' : [
                0.0,
                ("osc", "rotary1"),
            ],
            'decay': [
                1.0,
                ("osc", "rotary2"),
            ]
        }
        
        # The min and max can then be used to deterine the correct
        # position for a set of LEDs, depending on the note pressed.
        
        self.pos = int(abs((msg.note - self.min) * (1./(self.min-self.max))) * self.length)
        self.factor = round((1.0 / (self.max - self.min)) * self.length)

    def run(self, deltaMs):
        # Because this is a 'hold' animation:
        # When a key is held down, fade up into given color
        # At a rate determined by the "attack" parameter.
        self.refresh_params()
        rgb = self.hsb_to_rgb(self.hue, self.saturation, self.brightness)
        factor = 1.0
        if deltaMs < self.attack:
            factor = deltaMs / self.attack
        self.pixels[self.pos:self.pos+int(self.factor)] = rgb * factor
        
    def off(self, deltaMs):
        # When he key is let go off:
        # Fade down at a rate determined by the decay parameter.
        self.refresh_params()
        if deltaMs >= self.decay:
            self.pixes = [...]
            self.done = True
        else:
            factor = 1.0 - (deltaMs / self.decay)
            self.pixels = self.pixels_at_inflection * factor
        self.fade_down(deltaMs, self.decay + 0.01)