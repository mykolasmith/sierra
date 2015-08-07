import sys
import mido
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("midi.log")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print mido.get_input_names()
    else:
        bus = mido.open_input(mido.get_input_names()[int(sys.argv[1])])
        while True:
            for msg in bus.iter_pending():
                if not msg.type == 'clock':
                    log.info(msg)