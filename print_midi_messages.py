import mido

if __name__ == '__main__':
    bus = mido.open_input("IAC Driver Bus 1")
    while True:
        for msg in bus.iter_pending():
            print msg