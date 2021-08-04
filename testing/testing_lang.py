import requests
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
import time
from config.mischbares_small import config
from config.sdc_1 import config
#import json
#from copy import copy
#import requests
#import os
#from importlib import import_module
#helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
#sys.path.append(os.path.join(helao_root, 'config'))

#config = import_module(sys.argv[1]).config
#serverkey = sys.argv[2]

def test_fnc(action, params):
    server = 'lang'
    action = action 
    params = params
    r = requests.get("http://{}:{}/{}/{}".format(
        config['servers']['lang']['host'], 
        config['servers']['lang']['port'],server , action),
        params= params).json()
    print(r)


test_fnc('getPos', None)
test_fnc('moveRel', dict(dx=0, dy=0, dz=0)) 
test_fnc('moveAbs', dict(dx=2, dy=0, dz=0))  #[30.0, 80.0, 9.75] #[30.0, 100.0, 0.0]
test_fnc('moveWaste', dict(x=0, y=0, z=0))
test_fnc('moveHome', None)
test_fnc('moveDown', dict(dz=0.05, steps=169, maxForce=0.0065, threshold= 0.051)) #maximum length that you can go down is 5  #dz=0.321, steps=20, maxForce=0.08, threshold= 0.322
#dz=0.180, steps=80, maxForce=0.44, threshold= 0.190
# 169 steps each step 0.05 mm 
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
    dx = config['langDriver']['safe_sample_pos'][0] + x[j]
    dy = config['langDriver']['safe_sample_pos'][1] + y[j]
    dz = config['langDriver']['safe_sample_pos'][2]
    print("{},{},{}".format(dx, dy, dz))
    test_fnc('moveAbs', dict(dx=dx, dy=dy, dz=dz))
    #sleep(10)
    

    
