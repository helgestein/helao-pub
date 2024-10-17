import requests
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
import time
#from config.mischbares_small import config
from config.sdc_cyan import config
import requests

def force_test(action, params):
    server = 'force'
    action = action
    params = params
    res = requests.get("http://{}:{}/{}/{}".format(
        config['servers']['force']['host'], 
        config['servers']['force']['port'],server , action),
        params= params).json()
    return res

force_test('read', None)
force_test('setzero', None)

