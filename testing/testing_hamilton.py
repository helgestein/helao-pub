import requests
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
import time
from config.sdc_4 import config

def hamilton_test(action, params):
    server = 'hamilton'
    action = action
    params = params
    res = requests.get("http://{}:{}/{}/{}".format(
        config['servers']['hamilton']['host'], 
        config['servers']['hamilton']['port'], server , action),
        params= params).json()
    return res

hamilton_test('pumpL', params=dict(volume= 100, times= 1)) #volume in uL
hamilton_test('pumpR', params=dict(volume= 100, times= 1)) #volume in uL