import numpy as np
import gevent
import time

from gevent.queue import Queue

class Strip(object):
    
    def __init__(self, length):
        print 'Created strip %s of length %s' % (self, length)
        self.frame = np.array([(0,0,0)] * length)
        self.length = length
        self.holds = {}
        self.oneshots = {}
        
        self.tasks = Queue()
        self.expire = Queue()
        
        self.greenlets = []

    def aggregator(self):
        while True:
            t0 = time.time()
            
            if self.holds or self.oneshots:
                self.frame = np.maximum.reduce(
                    [ anim.get_frame() for anim in self.oneshots.itervalues() ] +
                    [ anim.get_frame() for anim in self.holds.itervalues() ]
                )
            
            gevent.sleep(time.time() - t0)
            
    def worker(self):
        while True:
            t0 = time.time()
            if self.greenlets:
                gevent.joinall(self.greenlets)
                self.greenlets = []
            gevent.sleep(0)
            
    def firing(self):
        while True:
            t0 = time.time()
            while not self.tasks.empty():
                task = self.tasks.get()
                if task['msg'].note not in self.holds:
                    event = gevent.spawn(
                        task['animation'],
                        task['strip'],
                        task['controller'],
                        task['msg']
                    )
                    self.greenlets.append(event)
            gevent.sleep(0)

    def expiry(self):
        while True:
            t0 = time.time()
            while not self.expire.empty():
                expiry = self.expire.get()
                anim = self.holds.get(expiry.note)
                if anim:
                    gevent.killall(anim.greenlets)
                    expire = gevent.spawn(anim.off)
                    self.greenlets.append(expire)
            gevent.sleep(0)
            
    def print_events(self):
        while True:
            print self.holds
            print self.oneshots
            gevent.sleep(1/3.)