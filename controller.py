import mido

class MidiController(object):
    
    def __init__(self, bus, mappings={}):
        print 'Connecting to MIDI port: %s' % bus
        self.bus = mido.open_input(bus)
        self.mappings = mappings
        self.controls = dict( (channel, {}) for channel in xrange(1,17) )
        self.triggers = dict( (channel, {}) for channel in xrange(1,17) )
        
    def listen(self):
        for msg in self.bus.iter_pending():
            self.dispatch(msg)
            
    def dispatch(self, msg):
        msg.channel += 1 # Ableton indexes from 1
        if msg.type == 'note_on':
            self.note_on(msg)
        elif msg.type == 'note_off':
            self.note_off(msg)
        elif msg.type == 'control_change':
            self.update_control(msg)
        
    def add_trigger(self, notes, channel, animation, strips):
        for note in notes:
            self.triggers[channel][note] = {
                'animation' : animation,
                'strips'    : strips
            }
        
    def set_channel(self, channel):
        self.channel = channel
        
    def note_on(self, msg):
        if msg.note in self.triggers[msg.channel]:
            mapping = self.triggers.get(msg.channel).get(msg.note)
            for strip in mapping.get('strips'):
                strip.note_on.put({
                    'strip' : strip,
                    'animation' : mapping.get('animation'),
                    'msg' : msg,
                })
    
    def note_off(self, msg):
        if msg.note in self.triggers[msg.channel]:
            mapping = self.triggers.get(msg.channel).get(msg.note)
            for strip in mapping.get('strips'):
                strip.note_off.put(msg)
            
    def update_control(self, msg):
        self.controls[msg.channel][msg.control] = msg.value
        
    def get(self, param_name, default):
        param = self.mappings.get(param_name)
        return self.controls.get(self.channel).get(param, default)
        
class MasterController(object):
    
    def __init__(self, controllers):
        self.controllers = controllers
        
    def via_channel(self, channel):
        for controller in self.itervalues():
            controller.set_channel(channel)
    
    def get(self, controller_name, param_name, default):
        if controller_name in self.controllers:
            return self.controllers[controller_name].get(param_name, default)
        return default
        
    def itervalues(self, *args, **kwargs):
        return self.controllers.itervalues()