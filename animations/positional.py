from base import Animation

class Positional(Animation):
    
    def __init__(self, length, controllers, msg, notes):
        super(Positional, self).__init__(length, controllers, msg, notes, 'hold')
        
        self.min = min(notes)
        self.max = max(notes)
        
        self.decay = 1.0
        self.pos = int(abs((msg.note - self.min) * (1./(self.min-self.max))) * self.length)
        self.factor = round((1.0 / (self.max - self.min)) * self.length)

    def run(self, deltaMs):
        hue = self.controllers.get(self.msg.channel, "mpk49", 12, 64)
        saturation = self.controllers.get(self.msg.channel, "nexus", "color", 127)
        brightness = self.controllers.get(self.msg.channel, "mpk49", "master", 127)
        
        rgb = self.hsb_to_rgb(hue, saturation, brightness)
        self.pixels[self.pos:self.pos+int(self.factor)] = rgb
        
    def off(self, deltaMs):
        self.fade_down(deltaMs, self.decay)