import time
import opc
import numpy as np

from handler import Handler

class Universe(object):

    def __init__(self, client, strips, controllers, max_pixels, fps):
        print 'Maximum pixels per channel: {0}'.format(max_pixels)
        print 'Starting Universe...'

        # The Handler makes sure we're doing the least
        # number of computations that are need,
        # by grouping animations by strip length.
        # e.g. { 50: MotionTween, 300: MotionTween }
        # And then copying the group frame to individual strip frames.

        handler = Handler(strips, controllers)

        # Beaglebone / LEDscape/ WS2812 hardware constraint requires all channels
        # to be the same # of LEDs. Generally, not an issue as most strips are
        # 300 LEDs (5m) or less.

        while True:

            # Easy to implement new controller types
            # as long as it implements a listen method.
            for controller in controllers.itervalues():
                controller.listen()

            now = time.time()
            # Schedule new animations (note_on)
            handler.note_on(now)
            # Toggle or switch animation mode
            handler.note_off(now)
            # Update animation frames for given time
            handler.worker(now)


            for strip in strips:
                strip.aggregate()
                #strip.pixels.resize((max_pixels,3))

            pixels = np.concatenate([
                strip.pixels.astype(np.uint8)
                for strip in strips
            ])

            client.put_pixels(pixels)

            handler.expire()

            time.sleep(fps)
