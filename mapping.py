import gevent

class Mapping(object):
    
    def __init__(self, controller):
        print 'Created mapping...'
        self.controller = controller
        self.animations = dict()
        self.inputs = dict()
        self.strips = dict()
        
    def add(self, strips=None, channel=None, note=None, animation=None, inputs=[]):
        if not channel in self.strips:
            self.strips.update({ channel: dict() })
        if not channel in self.inputs:
            self.inputs.update({ channel: dict() })
            
        self.strips[channel].update({ note: strips })
        self.inputs[channel].update({ note: inputs })
        
        if not channel in self.animations:
            self.animations.update({ channel : dict() })
        self.animations[channel].update({note: animation})
        for control in inputs:
            self.controller.add_control(channel, control)
            
    def remove(self, channel, note):
        self.strips[channel].update({ note: dict() })
        self.inputs[channel].update({ note: dict() })
        self.animations[channel].update({ note : dict() })
        
    def fire(self, msg):
        animation = self.animation_for(msg.channel, msg.note)
        if msg.note in self.strips[msg.channel]:
            for strip in self.strips[msg.channel][msg.note]:
                self.controller.universe.tasks.put({
                    'animation' : animation,
                    'strip'     : strip,
                    'controller': self.controller,
                    'msg'       : msg,
                })
            
    def expire(self, msg):
        release = []
        if msg.note in self.strips[msg.channel]:
            for strip in self.strips[msg.channel][msg.note]:
                if msg.note in strip.active_events['hold']:
                    animation = strip.active_events['hold'][msg.note]
                    release.append(gevent.spawn(animation.off))
        gevent.joinall(release)
        
    def animation_for(self, channel, note):
        if note in self.animations[channel]:
            return self.animations[channel][note]