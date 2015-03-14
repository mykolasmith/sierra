import gevent
import mido
import time

class MixerController(object):
    def __init__(self, bus, midi_controller):
        # Nexus 900
        print 'Connecting to MIDI port: %s' % bus
        self.bus = mido.open_input(bus)
        self.midi_controller = midi_controller
        
    def listener(self):
        while True:
            if self.bus.pending(): # Try commenting out?
                gevent.joinall([
                    gevent.spawn(self.update_global, msg)
                    for msg in self.bus.iter_pending()
                    if  msg.type == 'control_change'
                ])
            gevent.sleep(0)
            
    def update_global(self, msg):
        if msg.control in [5,10,22,83]:
            self.midi_controller.globals.update({ 'color' : msg.value+1 })

class MidiController(object):
    
    def __init__(self, bus):
        # MPK, APC, etc.
        print 'Connecting to MIDI port: %s' % bus
        self.bus = mido.open_input(bus)
        
        self.controls = dict()
        self.globals = dict()
        
        self.master = False
        self.pitchwheel = False
        
    def controls_for(self, channel, inputs):
        return [ self.get_control(channel, control) for control in inputs ]
    
    def pitchwheel_for(self, channel):
        return self.controls[channel]['pitchwheel']
    
    def master_for(self, channel):
        return self.controls[channel][1]
        
    def add_control(self, channel, control):
        if not channel in self.controls:
            self.controls[channel] = dict()
        self.controls[channel].update({ control : 0 })
        
    def use_master(self, channel):
        self.master = True
        if not 1 in self.controls[channel]:
            self.controls[channel].update({ 1 : 127 })
        
    def use_pitchwheel(self, channel):
        self.pitchwheel = True
        if not 'pitchwheel' in self.controls[channel]:
            self.controls[channel].update({ 'pitchwheel' : 0 })
        
    def update_control(self, msg):
        self.controls[msg.channel].update({ msg.control : msg.value })
        
    def update_pitchwheel(self, msg):
        self.controls[msg.channel].update({ 'pitchwheel' : msg.pitch })
        
    def get_control(self, channel, control):
        return self.controls[channel][control]
        
    def listener(self):
        while True:
            t0 = time.time()
            if self.bus.pending(): # Try commenting out?
                gevent.joinall([
                    gevent.spawn(self.dispatch, msg)
                    for msg in self.bus.iter_pending()
                ])
            gevent.sleep(0)
            
    def dispatch(self, msg):
        msg.channel += 1 # Ableton indexes from 1
        if msg.type == 'note_on':
            gevent.spawn(self.mapping.fire, msg).join()
        if msg.type == 'note_off':
            gevent.spawn(self.mapping.expire, msg).join()
        if msg.type == 'control_change':
            gevent.spawn(self.update_control, msg).join()
        if msg.type == 'pitchwheel':
            gevent.spawn(self.update_pitchwheel, msg).join()
