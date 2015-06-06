import mido
import re

from OSC import OSCServer
from handler import Handler

class MidiController(object):
    
    def __init__(self, bus, mappings={}):
        print 'Connecting to MIDI port: %s' % bus
        self.bus = mido.open_input(bus)
        self.mappings = mappings
        self.controls = dict( (channel, {}) for channel in xrange(1,17) )
        self.triggers = dict( (channel, {}) for channel in xrange(1,17) )
        
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
            
    def update_control(self, msg):
        self.controls[msg.channel][msg.control] = msg.value
        
    def get(self, channel, param, default):
        param = self.mappings.get(param)
        return self.controls.get(channel).get(param, default)
        
class OSCController(object):
    
    def __init__(self, client_address, port, mappings={}):
        print 'Connecting to OSC server at: %s:%s' % (client_address, port)
        self.server = OSCServer((client_address, port))
        self.server.timeout = 0
        self.controls = dict( (channel, {}) for channel in xrange(1,17) )
        self.triggers = dict( (channel, {}) for channel in xrange(1,17) )
        
    def get(self, channel, param, default):
        return self.controls[channel].get(param, default)
        
    def listen(self):
        self.server.noCallback_handler = self.dispatch # TODO: Does this need to be here?
        self.server.handle_request()
        
    def add_trigger(self, pattern, channel, animation, strips):
        
        #definition = re.search(r"\/([0-9]+)([/])([A-Za-z0-9]+)", p)
        
        expr = pattern.split('/')[1:]
        component = expr.pop(0)
        
        # (row * num_col) + col
        
        if len(expr) > 1:
            # multi-dimensional, e.g. '/multipush1/2/5'
            cols, rows = expr
            cols, rows = int(cols), int(rows)
            template = '/{0}/{1}/{2}'
            for col in xrange(1, cols + 1):
                for row in xrange(1, rows + 1):
                    trigger = template.format(component, col, row)
                    print trigger
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
                print pattern
                
                print expr
                print mapping.get('notes')
                
                row = int(expr[2]) - 1
                col = int(expr[1]) - 1
                num_cols = mapping.get('notes')[0]
                
                note = ((row * num_cols) + col)
                if data == 1.0:
                    msg = mido.Message(type="note_on", note=note, channel=channel)
                    self.handler.on.put({
                        'strips': mapping.get('strips'),
                        'animation': mapping.get('animation'),
                        'notes': mapping.get('notes'),
                        'msg': msg
                    })
                if data == 0.0:
                    msg = mido.Message(type="note_off", note=note, channel=channel)
                    self.handler.off.put(msg)
            
        
class MasterController(object):
    
    def __init__(self, controllers):
        self.controllers = controllers
        
    def bind(self, handler):
        if type(handler) == Handler:
            for controller in self.controllers.itervalues():
                controller.handler = handler
    
    def get(self, channel, controller_name, param_name, default):
        if controller_name in self.controllers:
            return self.controllers[controller_name].get(channel, param_name, default)
        return default
        
    def itervalues(self, *args, **kwargs):
        return self.controllers.itervalues()