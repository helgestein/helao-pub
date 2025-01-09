import requests
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
import time
#from config.mischbares_small import config
from config.sdc_1 import config

def pump_test(action, params):
    server = 'pump'
    action = action
    params = params
    res = requests.get("http://{}:{}/{}/{}".format(
        config['servers']['pump']['host'], 
        config['servers']['pump']['port'],server , action),
        params= params).json()
    return res

def mini_pump_test(action, params):
    server = 'minipump'
    action = action
    params = params
    res = requests.get("http://{}:{}/{}/{}".format(
        config['servers']['minipump']['host'], 
        config['servers']['minipump']['port'],server , action),
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
mini_pump_test('formulation', params=dict(speed= 80, volume= 100, direction= 1))                      