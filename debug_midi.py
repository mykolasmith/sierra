import mido
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("midi.log")

if __name__ == '__main__':
    bus = mido.open_input("IAC Driver Bus 2")
    #bus = mido.open_input("DJM-900nexus")
    while True:
        for msg in bus.iter_pending():
            log.info(msg)