import mido
import logging

log = logging.getLogger("/Users/M/sierra/midi.log")

if __name__ == '__main__':
    bus = mido.open_input("IAC Driver Bus 1")
    while True:
        for msg in bus.iter_pending():
            log.info(msg)