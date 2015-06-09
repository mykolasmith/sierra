import mido
import re

from OSC import OSCServer
from handler import Handler
from message import OSCMetaMessage

class MasterController(object):
    
    def __init__(self, controllers):
        self.controllers = controllers
        
    def parse(self, channel, params):
        result = dict()
        for param, conditions in params.iteritems():
            default = None
            value = None
            for condition in conditions:
                if type(condition) in (int, float):
                    default = condition
                else:
                    controller, accessor = condition
                    if controller in self.controllers:
                        value = self.controllers[controller].get(channel, accessor)
                        if value is not None:
                            break
            if value:
                result.update({ param : value })
            else:
                result.update({ param : default })
        return result
        
    def bind(self, handler):
        if type(handler) == Handler:
            for controller in self.controllers.itervalues():
                controller.handler = handler
    
    def get(self, channel, controller_name, param, default):
        if controller_name in self.controllers:
            return self.controllers[controller_name].get(channel, param, default)
        return default
        
    def itervalues(self, *args, **kwargs):
        return self.controllers.itervalues()

class MidiController(object):
    
    def __init__(self, bus):
        print 'Connecting to MIDI port: %s' % bus
        self.bus = mido.open_input(bus)
        self.controls = dict( (channel, {}) for channel in xrange(1,17) )
        self.triggers = dict( (channel, {}) for channel in xrange(1,17) )
        
    def normalize(self, val):
        return val / 127.
        
    def listen(self):
        for msg in self.bus.iter_pending():
            if msg.channel <= 15:
                msg.channel += 1
            self.dispatch(msg)
            
    def dispatch(self, msg):
        
        if msg.type == 'note_on':
            self.note_on(msg)
        elif msg.type == 'note_off':
            self.note_off(msg)
        elif msg.type == 'control_change':
            self.update_control(msg)
        elif msg.type == 'pitchwheel':
            self.update_pitchwheel(msg)
        
    def add_trigger(self, notes, channel, animation, strips):
        for note in notes:
            self.triggers[channel][note] = {
                'animation' : animation,
                'strips'    : strips,
                'notes'     : notes
            }
        
    def note_on(self, msg):
        if msg.note in self.triggers[msg.channel]:
            mapping = self.triggers.get(msg.channel).get(msg.note)
            self.handler.on.put({
                'strips' : mapping.get('strips'),
                'animation' : mapping.get('animation'),
                'notes' : mapping.get('notes'),
                'msg' : msg,
            })
    
    def note_off(self, msg):
        if msg.note in self.triggers[msg.channel]:
            self.handler.off.put(msg)
            
    def update_pitchwheel(self, msg):
        self.controls[msg.channel].update({ 'pitchwheel' : msg.pitch })
            
    def update_control(self, msg):
        val = self.normalize(msg.value)
        self.controls[msg.channel].update({ msg.control : val })
        
    def get(self, channel, param):
        return self.controls.get(channel).get(param, None)
        
class OSCController(object):
    
    def __init__(self, client_address, port):
        print 'Connecting to OSC server at: %s:%s' % (client_address, port)
        self.server = OSCServer((client_address, port))
        self.server.timeout = 0
        self.controls = dict( (channel, {}) for channel in xrange(1,17) )
        self.triggers = dict( (channel, {}) for channel in xrange(1,17) )
        
    def get(self, channel, param):
        return self.controls[channel].get(param, None)
        
    def listen(self):
        self.server.noCallback_handler = self.dispatch # TODO: Does this need to be here?
        self.server.handle_request()
        
    def add_trigger(self, pattern, channel, animation, strips):
        expr = pattern.split('/')[1:]
        component = expr.pop(0)
        
        if len(expr) > 1:
            # multi-dimensional, e.g. '/multipush1/2/5'
            cols, rows = expr
            cols, rows = int(cols), int(rows)
            template = '/{0}/{1}/{2}'
            for col in xrange(1, cols + 1):
                for row in xrange(1, rows + 1):
                    trigger = template.format(component, col, row)
                    self.triggers[channel].update({ trigger : {
                        'animation' : animation,
                        'strips'    : strips,
                        'notes'     : [cols, rows]
                    }})
        else:
            self.triggers[channel].update({ trigger : {
                'animation': animation,
                'strips': strips,
                'notes': [0]
            }})
        
    def dispatch(self, pattern, tags, data, addr):
        expr = pattern.split('/')[1:]
        channel = int( expr.pop(0) )
        
        if len(data) == 1:
            data = data.pop()
        
        if len(expr) > 1:
            # multi-dimensional 
            pattern = '/' + '/'.join(expr)
            if pattern in self.triggers[channel]:
                mapping = self.triggers.get(channel).get(pattern)
                
                row = int(expr[2]) - 1
                col = int(expr[1]) - 1
                num_cols = mapping.get('notes')[0]
                
                note = ((row * num_cols) + col)
                if data == 1.0:
                    msg = OSCMetaMessage(note=note, pattern=pattern, channel=channel)
                    self.handler.on.put({
                        'strips': mapping.get('strips'),
                        'animation': mapping.get('animation'),
                        'notes': mapping.get('notes'),
                        'msg': msg
                    })
                if data == 0.0:
                    msg = OSCMetaMessage(note=note, pattern=pattern, channel=channel)
                    self.handler.off.put(msg)