from force_driver import MEGSV
from mischbares_small import config

f = MEGSV(config['force'])

def read():
    while True:
        val = f.read()
        if f != None:
            break
    return val