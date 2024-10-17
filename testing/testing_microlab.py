import requests
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
import time
from config.sdc_4 import config

def microlab_test(action, params):
    server = 'microlab'
    action = action
    params = params
    res = requests.get("http://{}:{}/{}/{}".format(
        config['servers']['microlab']['host'], 
        config['servers']['microlab']['port'], server , action),
        params= params).json()
    return res

microlab_test('pumpL', params=dict(volume= 100, times= 1)) #volume in uL
microlab_test('pumpR', params=dict(volume= 100, times= 1)) #volume in uL