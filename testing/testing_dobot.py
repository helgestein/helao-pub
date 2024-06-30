import sys
from copy import copy
import os

import requests
from config.sdc_cyan import config

def dobot_fnc(action, params):
    server = 'dobot'
    action = action 
    params = params
    r = requests.get("http://{}:{}/{}/{}".format(
        config['servers']['dobot']['host'], 
        config['servers']['dobot']['port'],server , action),
        params= params).json()
    print(r)

# test these functions after the safe positions are defined

dobot_fnc('moveHome', None)
dobot_fnc('moveWaste', dict(x=0, y=0, z=0, r=0))
dobot_fnc('moveSample', dict(x=0, y=0, z=0, r=0))
dobot_fnc('removeDrop', dict(x=0, y=0, z=0, r=0)) # when tip is used

dobot_fnc('moveDown', dict(dz=0.05, steps=50, maxForce=50, threshold=0.1)) # threshold for dz, dz should be positive (despite the move down is negative)

dobot_fnc('getPos', None)

#dobot_fnc('removeDropEdge', dict(x=0, y=0, z=0, r=0)) # when edge is used
#sample position 0, 0
#[271.283627, -27.79039, 100.0, 327.5]
#sample position upper corner +x,+y
#[319.283627, 22.20961, 100.5, 327.5]

dobot_fnc('moveJointAbsolute', dict(x=0, y=0, z=0, r=0))
dobot_fnc('moveJointRelative', dict(x=0, y=0, z=0, r=0))
dobot_fnc('moveAbs', dict(x=0, y=0, z=0, r=0))
#dobot_fnc('moveRel', dict(x=0, y=0, z=0, r=0))
dobot_fnc('setJointSpeed', dict(speed=3))
dobot_fnc('setLinearSpeed', dict(speed=3))
dobot_fnc('getAngles', None)
dobot_fnc('getErrorID', None)

dobot_fnc('openGripper', None)
dobot_fnc('closeGripper', None)
dobot_fnc('suck', None)
dobot_fnc('unsuck', None)

dobot_fnc('shutdown', None)
    
#sys.path.append(r'../config')
#sys.path.append(r'../action')
#sys.path.append(r'../server')
#import time
#from config.mischbares_small import config
#import json
#import requests
#from importlib import import_module
#helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
#sys.path.append(os.path.join(helao_root, 'config'))

#config = import_module(sys.argv[1]).config
#serverkey = sys.argv[2]