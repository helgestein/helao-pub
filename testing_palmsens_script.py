import requests
from config.sdc_cyan import config

def echem_test(action, params):
    server = 'palmsens'
    action = action
    params = params
    res = requests.get("http://{}:{}/{}/{}".format(
        config['servers']['palmsens']['host'], 
        config['servers']['palmsens']['port'], server, action),
        params= params).json()
    return res

print("PalmSens testing")
print("Functions examples:")
print("echem_test('measure', params=dict(method='open_circuit_potentiometry', parameters=dict(t_run= 1, t_interval= 0.5), filename='dummy_cell_test_ocp_2'))")
