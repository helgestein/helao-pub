import requests
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
import time
from mischbares_small import config
import json
from copy import copy

def pump_test(action, params):
    server = 'pumping'
    action = action
    params = params
    res = requests.get("http://{}:{}/{}/{}".format(
        config['servers']['pumpingServer']['host'], 
        config['servers']['pumpingServer']['port'],server , action),
        params= params).json()
    return res

pump_test('formulation', params=dict(
    comprel='[0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125]',
    pumps= '[0, 1, 2, 4, 6, 7, 10, 12]',
    speed= 8000, totalvol=2000))

pump_test('flushSerial', None)
pump_test('resetPrimings', None)
pump_test('getPrimings', None)
pump_test('refreshPrimings', None)
