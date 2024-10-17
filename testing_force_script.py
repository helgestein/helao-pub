import requests
from config.sdc_cyan import config

def force_test(action, params):
    server = 'force'
    action = action
    params = params
    res = requests.get("http://{}:{}/{}/{}".format(
        config['servers']['force']['host'], 
        config['servers']['force']['port'],server , action),
        params= params).json()
    return res

print("Force testing")
print("Functions examples:")
print("force_test('read', None)")
print("force_test('setzero', None)")
