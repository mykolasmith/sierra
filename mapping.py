import gevent

class MidiMapping(object):
    
    def __init__(self, controller):
        print 'Created mapping...'
        self.map = dict()
        self.controller = controller
        self.controller.mapping = self
        
    def add(self, strips=None, channel=None, notes=None, animation=None, inputs=[]):
            
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
            
    def remove(self, channel, note):
        self.map[channel].update({ note: dict() })

    def fire(self, msg):
        animation = self.animation_for(msg.channel, msg.note)
        if msg.note in self.map[msg.channel]:
            for strip in self.map[msg.channel][msg.note]['strips']:
                self.controller.universe.tasks.put({
                    'animation' : animation,
                    'strip'     : strip,
                    'controller': self.controller,
                    'msg'       : msg,
                })
            
    def expire(self, msg):
        parent = []
        off = []
        if msg.note in self.map[msg.channel]:
            for strip in self.map[msg.channel][msg.note]['strips']:
                if msg.note in strip.active_events['hold']:
                    animation = strip.active_events['hold'][msg.note]
                    parent.append(gevent.spawn(animation.kill_parent_greenlet))
                    off.append(gevent.spawn(animation.off))
        gevent.joinall(parent)
        gevent.joinall(off)
        
    def animation_for(self, channel, note):
        if note in self.map[channel]:
            return self.map[channel][note]['animation']
            
    def inputs_for(self, channel, note):
        if note in self.map[channel]:
            return self.map[channel][note]['inputs']