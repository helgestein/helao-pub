import requests
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
import time
from config.mischbares_small import config
import json
from copy import copy

def pump_test(action, params):
    server = 'pumping'
    action = action
    params = params
    res = requests.get("http://{}:{}/{}/{}".format(
        config['servers']['minipumpServer']['host'], 
        config['servers']['minipumpServer']['port'],server , action),
        params= params).json()
    return res

def mini_pump_test(action, params):
    server = 'minipumping'
    action = action
    params = params
    res = requests.get("http://{}:{}/{}/{}".format(
        config['servers']['minipumpingServer']['host'], 
        config['servers']['minipumpingServer']['port'],server , action),
        params= params).json()
    return res

#pump
pump_test('formulation', params=dict(
    comprel='[0.5]',
    pumps= '[0]',
    speed= 400, totalvol=20, direction= 1))

pump_test('flushSerial', None)
pump_test('resetPrimings', None)
pump_test('getPrimings', None)
pump_test('refreshPrimings', None)

#mini pump
mini_pump_test('formulation', params=dict(speed= 80, volume= 500, direction= 1))                      