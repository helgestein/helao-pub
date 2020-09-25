import requests
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
import time
from mischbares_small import config
import json
from copy import copy

def echem_test(action, params):
    server = 'echem'
    action = action
    params = params
    res = requests.get("http://{}:{}/{}/{}".format(
        config['servers']['echemServer']['host'], 
        config['servers']['echemServer']['port'],server , action),
        params= params).json()
    return res

# test all the actions    
echem_test('potential', None)
echem_test('ismeasuring', None)
echem_test('current', None)
echem_test('appliedpotential', None)
echem_test('setCurrentRange', dict(crange='10mA'))
echem_test('cellonoff', dict(onoff='off'))

echem_test('measure', params=dict(procedure="ca", setpointjson="{'applypotential': {'Setpoint value': 0.01}, 'recordsignal': {'Duration': 10}}",
                        plot="tCV",
                        onoffafter="off",
                        safepath="C:/Users/SDC_1/Documents/deploy/helao-dev/temp",
                        filename="ca.nox",
                        parseinstructions="recordsignal"))

#echem_test('retrieve', params=??)

