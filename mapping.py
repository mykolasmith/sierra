class MidiMapping(object):
    
    def __init__(self, controller):
        print 'Created mapping...'
        self.map = dict()
        self.controller = controller
        self.controller.mapping = self
        
    def add(self, strips=None, channel=None,  animation=None, notes=[], inputs=[], master=False, pitchwheel=False):
            
        if not channel in self.map:
            self.map.update({ channel: dict() })
        
        for note in notes:
            self.map[channel].update({ note : {
                'strips' : strips,
                'inputs' : inputs,
                'animation' : animation }
            })
            
        for control in inputs:
            self.controller.add_control(channel, control)
            
        if master:
            self.controller.use_master(channel)
            
        if pitchwheel:
            self.controller.use_pitchwheel(channel)
            
    def remove(self, channel, note):
        self.map[channel].update({ note: dict() })
    
    def note_on(self, msg):
        animation = self.animation_for(msg.channel, msg.note)
        try:
            for strip in self.map[msg.channel][msg.note]['strips']:  
                strip.note_on.put({
                    'animation' : animation,
                    'msg'       : msg,
                    'strip'     : strip,
                    'controller': self.controller
                })
        except KeyError:
            pass
    
    def note_off(self, msg):
        try:
            for strip in self.map[msg.channel][msg.note]['strips']:
                strip.note_off.put(msg)
        except KeyError:
            pass

    def animation_for(self, channel, note):
        if note in self.map[channel]:
            return self.map[channel][note]['animation']
            
    def inputs_for(self, channel, note):
        if note in self.map[channel]:
            return self.map[channel][note]['inputs']