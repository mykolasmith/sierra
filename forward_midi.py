import mido
import time

if __name__ == '__main__':
    bridge = mido.open_input("TouchOSC Bridge")
    output = mido.open_output("IAC Driver Bus 2")
    while True:
        for msg in bridge.iter_pending():
            output.send(msg)
            time.sleep(1/100.)