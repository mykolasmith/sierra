import mido

from OSC import ThreadingOSCServer
from animation.base import Animation

class Parameter(object):

    def __init__(self, name=None, default=None, controls=None):
        if name is None:
            raise RuntimeError("Cannot add unnamed parameter.")

        self.name = name

        if default is None:
            default = 0.0
        self.default = default

        if controls is None:
            controls = []
        self.controls = controls

class MasterController(object):

    def __init__(self, controllers):
        # Hold all of the controllers in this class (MIDI, OSC, etc.)
        self.controllers = controllers

    def __getitem__(self, item):
        # Allow the master controller to be accessed like a normal dictionary.
        if item in self.controllers:
            return self.controllers[item]

    def itervalues(self, *args, **kwargs):
        # Iterate over the master controller's devices.
        return self.controllers.itervalues()

    def params(self, channel, params):
        # Parse a dictionary of parameters, patterns (conditions) and defaults
        # In order to determine the proper input source to use.
        # E.g. {0.5, ['osc', '/fader1'], ['midi', 16]}
        # The above example will check for a fader1 value from the OSC controller,
        # and if not found will check for control 16 from the midi controller,
        # and if neither are connected then it will return the default: 0.5
        result = dict()
        for param in params:
            value = None
            default = param.default
            for controller, accessor in param.controls:
                if controller in self.controllers:
                    value = self.controllers[controller].get(channel, accessor)
                    if value is not None:
                        break
            if value is not None:
                result.update({ param.name : value })
            else:
                result.update({ param.name : default })
        return result

class MidiController(object):

    def __init__(self, bus):
        print 'Connecting to MIDI port: %s' % bus
        self.bus = mido.open_input(bus)
        self.controls = dict( (channel, {}) for channel in xrange(1,17) )
        self.triggers = dict( (channel, {}) for channel in xrange(1,17) )

    def normalize(self, val):
        # Since we want to work with 0-1 decimal values
        # Automatically normalize incoming MIDI parameters.
        return val / 127.

    def listen(self):

        for msg in self.bus.iter_pending():
            # We increment channels by 1, since most DAWs index from 1
            # whereas the midi spec indexes from 0.
            # This should be applied at the GUI level instead.
            if msg.type in ('control_change, note_on, note_off'):
                if msg.channel < 15:
                    msg.channel += 1
                    self.dispatch(msg)


    def dispatch(self, msg):

        # Implementation of the MIDI spec would look something like this:
        # 0x90 == 'note_on', 0x80 == 'note_off', etc.
        # The "mido" package is  an awesome python library that encapsulates that for us.
        if msg.type == 'note_on':
            self.note_on(msg)
        elif msg.type == 'note_off':
            self.note_off(msg)
        elif msg.type == 'control_change':
            self.update_control(msg)
        elif msg.type == 'pitchwheel':
            self.update_pitchwheel(msg)

    def add_trigger(self, notes=None, channel=None, animation=None, strips=None, trigger=None, params=None):
        # This will map the given MIDI notes fired from a given MIDI channel,
        # to trigger an animation on the given LED strips.

        if notes is None:
            raise RuntimeError("MIDI trigger must reference a list of notes. E.g. [60] or xrange(60,70)")

        if channel is None:
            raise RuntimeError("MIDI trigger must reference a MIDI channel")
        if not 0 < channel <= 16:
            raise RuntimeError("MIDI trigger must reference a MIDI channel between 1 and 16")

        if animation is None:
            raise RuntimeError("MIDI trigger must reference an Animation class")

        if strips is None:
            raise RuntimeError("MIDI trigger must reference a list of Strip objects")

        if trigger is None:
            raise RuntimeError("MIDI trigger must specify a trigger mode. E.g. hold, oneshot, or toggle")

        print "Notes:", notes
        print "Channel:", channel
        print "Animation:", animation
        print "Trigger:", trigger
        print "Parameters:"
        for param in params:
            print "\t" , param.name, ":", param.default, ":" , param.controls
        print "----------------------"

        for note in notes:
            self.triggers[channel][note] = {
                'animation' : animation,
                'strips'    : strips,
                'notes'     : notes,
                'params'    : params,
                'trigger'   : trigger
            }

    def note_on(self, msg):
        if msg.note in self.triggers[msg.channel]:
            mapping = self.triggers.get(msg.channel).get(msg.note)
            self.handler.on.put({
                'strips' : mapping.get('strips'),
                'animation' : mapping.get('animation'),
                'notes' : mapping.get('notes'),
                'params' : mapping.get('params'),
                'trigger': mapping.get('trigger'),
                'msg' : msg,
            })

    def note_off(self, msg):
        if msg.note in self.triggers[msg.channel]:
            self.handler.off.put(msg)

    def update_pitchwheel(self, msg):
        self.controls[msg.channel].update({ 'pitch' : msg.pitch })

    def update_control(self, msg):
        val = self.normalize(msg.value)
        self.controls[msg.channel].update({ msg.control : val })

    def get(self, channel, param):
        return self.controls.get(channel).get(param, None)

class OSCController(object):

    def __init__(self, client_address, port):
        print 'Connecting to OSC server at: %s:%s' % (client_address, port)
        self.server = ThreadingOSCServer((client_address, port))
        self.server.callback = self.dispatch
        self.controls = dict( (channel, {}) for channel in xrange(1,17) )

    def get(self, channel, control):
        result = None
        if channel in self.controls:
            if control in self.controls[channel]:
                result = self.controls[channel][control]
        return result

    def listen(self):
        # This is kind of hacky right now
        # But instead of registering a callback for each pattern,
        # we just override the noCallback handler and handle everything
        # with a single dispatch function.
        self.server.handle_request()

    def dispatch(self, pattern, tags, data, addr):
        # For now only rotary and fader (i.e. control parameters) are implemented.
        # I prefer to leave the triggers to a MIDI controller.
        # Although, many OSC clients can mimic MIDI.
        # This is because it allows me stay within my Ableton / midi sequencer workflow
        # For looping / quantization of animations to a common tempo.

        expr = pattern.split('/')[1:]
        if len(expr) > 2:
            return

        channel, pattern = expr
        channel = int(channel)

        if len(data) == 1:
            data = data.pop()

        if pattern.find('rotary') >= 0 or\
           pattern.find('fader') >= 0:
            self.controls[channel].update({ pattern : data })
