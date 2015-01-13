import gevent
from gevent.event import Event
import numpy as np

class Animation(object):
    def __init__(self, channel, msg, trigger):
        self.msg = msg
        self.channel = channel
        self.trigger = trigger
        self.frame = np.array([(0,0,0)] * channel.length)
        self.stop = Event()
        
        if trigger == 'oneshot':
            self.accessor = id(self)
        if trigger == 'hold':
            self.accessor = msg.note
            
        self.channel.active_events[trigger][self.accessor] = self
        
    def expire(self):
        if self.accessor in self.channel.active_events[self.trigger]:
            self.channel.active_events[self.trigger].pop(self.accessor)
        
    def off(self):
        self.stop.set()
            
    def sleep(self, s):
        gevent.sleep(s)
        
    def spawn(self, f, *args, **kwargs):
        return gevent.spawn(f, *args, **kwargs)
        
    def joinall(self, greenlets):
        gevent.joinall(greenlets)
    
    def worker(self, *args, **kwargs):
        raise NotImplemented
        
class MotionTween(Animation):
    
    def __init__(self, channel, msg, trigger):
        # Begin an animation
        super(MotionTween, self).__init__(channel, msg, trigger)
        
        # Spawn + join from iterable to sequence individually
        for i in range(channel.length):
            self.spawn(self.worker, i, msg).join()
            
        # Joinall to sequence concurrently
        #self.joinall([
            #self.spawn(animation1, msg),
            #self.spawn(animation2, msg),
            #self.spawn(animation3, msg)
        #])
            
        # Expire the event when you're finished
        self.expire()
    
    def worker(self, i, msg):
        trail = list(xrange(1,5))
        for offset in trail:
            try:
                intensity = ((msg.velocity * 2)/((len(trail) * 1.0)/offset))
                if msg.note == 60:
                    self.frame[i+offset] = (intensity, 0, 0)
                if msg.note == 62:
                    self.frame[i+offset] = (0, intensity, 0)
                if msg.note == 64:
                    self.frame[i+offset] = (0, 0, intensity)
            except IndexError:
                pass
        self.frame[i] = (0,0,0)
        self.sleep(1/(1.0 * msg.velocity))
            
class Fade(Animation):
    
    def __init__(self, channel, msg, trigger):
        super(Fade, self).__init__(channel, msg, trigger)
        self.brightness = 0
        self.steps = [x for x in range(100) if  x % 6 == 0 ]
        for i in self.steps:
            if not self.stop.isSet():
                self.spawn(self.worker, i).join()
    
    def off(self):
        super(Fade, self).off()
        for i in reversed(self.steps):
            for led in range(self.channel.length):
                self.frame[led] = (0,0,i)
            self.sleep(1/1000.)
        self.sleep(0.)
    
    def worker(self, i):
        self.brightness = i #Saving brightness "state"
        for led in range(self.channel.length):
            self.frame[led] = (0, 0, i)
        self.sleep(1/1000.)