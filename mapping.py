import gevent

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

    def fire(self, msg):
        animation = self.animation_for(msg.channel, msg.note)
        if msg.note in self.map[msg.channel]:
            for strip in self.map[msg.channel][msg.note]['strips']:  
                strip.tasks.put({ # Find a way to attach the mapping to the universe
                    'animation' : animation, # Should we put the animation directly onto an event loop on the strip?
                    'msg'       : msg,
                    'strip'     : strip,
                    'controller': self.controller
                })
            
    def expire(self, msg):
        if msg.note in self.map[msg.channel]:
            for strip in self.map[msg.channel][msg.note]['strips']:
                if msg.note in strip.holds:
                    strip.expire.put(msg)

    def animation_for(self, channel, note):
        return self.map[channel][note]['animation']
            
    def inputs_for(self, channel, note):
        return self.map[channel][note]['inputs']