import requests
from config.sdc_cyan import config

def psd_test(action, params):
    server = 'psd'
    action = action
    params = params
    res = requests.get("http://{}:{}/{}/{}".format(
        config['servers']['force']['host'], 
        config['servers']['force']['port'], server, action),
        params= params).json()
    return res

print("PSD testing")
print("Functions examples:")
print("psd_test('pumpSimple', params=dict(volume= 200, valve = 2, speed = 10, times= 1))")
print("psd_test('pumpMix', params=dict(V1= 0, V2 = 200, V3 = 400, V4 = 0, V5 = 600, V6 = 0, speed = 10, mix = 1, times= 1))")
print("psd_test('pumpRead', None)")