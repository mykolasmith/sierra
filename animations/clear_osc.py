from base import Animation

class ClearOSC(Animation):
    
    def __init__(self, length, controllers, msg, notes):
        super(ClearOSC, self).__init__(length, controllers, msg, notes, 'oneshot')
        self.controllers.controllers['ipad'].controls = dict( (channel, {}) for channel in xrange(1,17) )
        print 'Cleared OSC: {0}'.format(self.controllers.controllers['ipad'].controls)
        self.done = True