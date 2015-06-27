import mido
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("midi.log")

if __name__ == '__main__':
    try:
        bus = mido.open_input("TouchOSC Bridge")
    except:
        bus = mido.open_input("IAC Driver Bus 1")
    while True:
        for msg in bus.iter_pending():
            log.info(msg)