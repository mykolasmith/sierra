import gevent
import mido

class MidiController(object):
    
    def __init__(self, bus):
        # MPK, APC, etc.
        print 'Connecting to MIDI port: %s' % bus
        self.bus = mido.open_input(bus)
        self.controls = dict()
        
    def controls_for(self, channel, inputs):
        return [ self.get_control(channel, control) for control in inputs ]
        
    def add_control(self, channel, control):
        if not channel in self.controls:
            self.controls[channel] = dict()
        self.controls[channel][control] = 0
        
    def update_control(self, msg):
        self.controls[msg.channel][msg.control] = msg.value
        
    def get_control(self, channel, control):
        if channel in self.controls:
            return self.controls[channel][control]
        
    def listener(self, universe):
        self.universe = universe
        while True:
            gevent.joinall([
                gevent.spawn(self.dispatch, msg)
                for msg in self.bus.iter_pending()
            ])
            gevent.sleep(0.)
            
    def dispatch(self, msg):
        msg.channel += 1
        if msg.type == 'note_on':
            gevent.spawn(self.universe.mapping.fire, msg).join()
        if msg.type == 'note_off':
            gevent.spawn(self.universe.mapping.expire, msg).join()
        if msg.type == 'control_change':
            gevent.spawn(self.update_control, msg).join()
