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

print("Dobot testing")
print("Functions examples:")
print("dobot_fnc('moveHome', None)")
print("dobot_fnc('moveWaste', dict(x=0, y=0, z=0, r=0))")
print("dobot_fnc('moveSample', dict(x=0, y=0, z=0, r=0))")
print("dobot_fnc('removeDrop', dict(x=0, y=0, z=0, r=0))")
print("dobot_fnc('moveDown', dict(dz=0.05, steps=50, maxForce=50, threshold=0.1))")
print("dobot_fnc('moveJointAbsolute', dict(x=0, y=0, z=0, r=0))")
print("dobot_fnc('moveJointRelative', dict(x=0, y=0, z=0, r=0))")
print("dobot_fnc('moveAbs', dict(x=0, y=0, z=0, r=0))")
print("dobot_fnc('moveRel', dict(x=0, y=0, z=0, r=0))")
print("dobot_fnc('setJointSpeed', dict(speed=3))")
print("dobot_fnc('setLinearSpeed', dict(speed=3))")
print("dobot_fnc('getPos', None)")
print("dobot_fnc('getAngles', None)")
print("dobot_fnc('getErrorID', None)")
print("dobot_fnc('openGripper', None)")
print("dobot_fnc('closeGripper', None)")
print("dobot_fnc('suck', None)")
print("dobot_fnc('unsuck', None)")
print("dobot_fnc('shutdown', None)")

