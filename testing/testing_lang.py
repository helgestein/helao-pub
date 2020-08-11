import requests
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
import time
from mischbares_small import config
import json
from copy import copy


server = 'motor'
action = 'getPos'
params = None
requests.get("http://{}:{}/{}/{}".format(
    config['servers']['motorServer']['host'], 
    config['servers']['motorServer']['port'],server , action),
    params= params,timeout=1).json()



server = 'motor'
action = 'moveRel'
params = dict(dx=-10, dy=-10, dz=-10)
requests.get("http://{}:{}/{}/{}".format(
    config['servers']['motorServer']['host'], 
    config['servers']['motorServer']['port'],server , action),
    params= params).json()


server = 'motor'
action = 'moveAbs'
params = dict(dx=10, dy=10, dz=10)
requests.get("http://{}:{}/{}/{}".format(
    config['servers']['motorServer']['host'], 
    config['servers']['motorServer']['port'],server , action),
    params= params).json()


server = 'motor'
action = 'moveHome'
params = None
requests.get("http://{}:{}/{}/{}".format(
    config['servers']['motorServer']['host'], 
    config['servers']['motorServer']['port'],server , action)).json()



server = 'motor'
action = 'moveWaste'
params = None
requests.get("http://{}:{}/{}/{}".format(
    config['servers']['motorServer']['host'], 
    config['servers']['motorServer']['port'],server , action)).json()

