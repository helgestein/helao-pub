import requests
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
import time
from config.mischbares_small import config
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
echem_test('setcurrentrange', params=dict(crange='10uA'))
echem_test('cellonoff', dict(onoff='off'))

echem_test('measure', params=dict(procedure="ca", setpointjson="{'applypotential': {'Setpoint value': 0.01}, 'recordsignal': {'Duration': 120}}",
                        plot="tCV",
                        onoffafter="off",
                        safepath="C:/Users/SDC_1/Documents/deploy/helao-dev/temp",
                        filename="ca.nox",
                        parseinstructions="recordsignal"))


echem_test('measure', params=dict(procedure="cv", setpointjson= json.dumps({'FHSetSetpointPotential': {'Setpoint value': -1}, 'FHWait': {'Time': 10}, 
                                        'CVLinearScanAdc164': {'StartValue': -1, 'UpperVertex': -0.5, 'LowerVertex':-1.5, 'NumberOfStopCrossings': 6, 'ScanRate': 0.1}}),
                                        plot="tCV",
                                        onoffafter="off",
                                        safepath="C:/Users/SDC_1/Documents/deploy/helao-dev/temp",
                                        filename="cv.nox",
                                        parseinstructions='CVLinearScanAdc164'))



echem_test('measure', params=dict(procedure="ca", setpointjson= json.dumps({'applypotential': {'Setpoint value': -1}, 'recordsignal': {'Duration': 120}}),
                                        plot="tCV",
                                        onoffafter="off",
                                        safepath="C:/Users/SDC_1/Documents/deploy/helao-dev/temp",
                                        filename="ca.nox",
                                        parseinstructions='recordsignal'))


echem_test('measure', params=dict(procedure="cp", setpointjson= json.dumps({'applycurrent0': {'Setpoint value': 10**-5},'applycurrent': {'Setpoint value': 10**-5}, 'recordsignal': {'Duration': 120}}),
                                plot="tCV",
                                onoffafter="off",
                                safepath="C:/Users/SDC_1/Documents/deploy/helao-dev/temp",
                                filename="cp.nox",
                                parseinstructions='recordsignal'))

echem_test('retrieve', params=??)

'''


'''