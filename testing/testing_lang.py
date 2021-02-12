import requests
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
import time
from config.mischbares_small import config
import json
from copy import copy

def test_fnc(action, params):
    server = 'motor'
    action = action 
    params = params
    r = requests.get("http://{}:{}/{}/{}".format(
        config['servers']['motorServer']['host'], 
        config['servers']['motorServer']['port'],server , action),
        params= params).json()
    print(r)


test_fnc('getPos', None)
test_fnc('moveRel', dict(dx=0, dy=0, dz=0)) 
test_fnc('moveAbs', dict(dx=2, dy=0, dz=0))  #[30.0, 80.0, 9.75] #[30.0, 100.0, 0.0]
test_fnc('moveWaste', dict(x=0, y=0, z=0))
test_fnc('moveHome', None)
test_fnc('moveDown', dict(dz=0.213, steps=120, maxForce=0.44, threshold= 0.320)) #maximum length that you can go down is 5  #dz=0.321, steps=20, maxForce=0.08, threshold= 0.322
#dz=0.180, steps=80, maxForce=0.44, threshold= 0.190
test_fnc('moveSample', dict(x=0, y=0, z=0))
test_fnc('RemoveDroplet', dict(x=0, y=0, z=0))

# 0.020
import numpy as np
import matplotlib.pyplot as plt
x, y = np.meshgrid([4 * i for i in range(8)], [4 * i for i in range(8)])
x, y = x.flatten(), y.flatten()
plt.scatter(x, y)
plt.show()

from time import sleep
for j in range(64):
    print("{}, {}".format(x[j], y[j]))
    dx = config['lang']['safe_sample_pos'][0] + x[j]
    dy = config['lang']['safe_sample_pos'][1] + y[j]
    dz = config['lang']['safe_sample_pos'][2]
    print("{},{},{}".format(dx, dy, dz))
    test_fnc('moveAbs', dict(dx=dx, dy=dy, dz=dz))
    #sleep(10)
    

    
