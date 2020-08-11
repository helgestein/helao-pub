import requests
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
sys.path.append(r'../orchestrators')

import time
from mischbares_small import config
import json
from copy import copy

def test_fnc(sequence):
    server = 'orchestrator'
    action = 'addExperiment'
    params = dict(experiment=json.dumps(sequence))
    requests.post("http://{}:{}/{}/{}".format(
    config['servers']['orchestrator']['host'] ,13380 ,server ,action),
    params= params).json()

#################sequesnce of the lang_motor action
lang_sequence= dict(soe=['motor/getPos_0', 'motor/moveRel_0', 'motor/moveAbs_0',
                         'motor/moveHome_0','motor/moveWaste_0', 'motor/getPos_1'], 
                    params= dict(getPos_0 = None, moveRel_0= dict(dx=10, dy=10, dz=10),
                                moveAbs_0= dict(dx=0, dy=0, dz=0), moveHome_0= None,
                                moveWaste_0= None, getPos_1= None),
                    meta=dict(ma=1 , substrate=1))

test_fnc(lang_sequence)

#################sequence of echem functions 
echem_sequence = dict(soe= ['echem/potential_0', 'echem/ismeasuring_0',
                            'echem/current_0', 'echem/appliedpotential_0', 'echem/setCurrentRange_0',
                            'echem/cellonoff_0', 'echem/measure_0'],
                    params= dict(potential_0 = None, ismeasuring_0= None, current_0= None,
                             appliedpotential_0= None, setCurrentRange_0= dict(crange='10mA'),
                             cellonoff_0= dict(onoff='off'), measure_0= dict(procedure="ca", setpointjson="{'applypotential': {'Setpoint value': 0.01}, 'recordsignal': {'Duration': 10}}",
                        plot="tCV",
                        onoffafter="off",
                        safepath="C:/Users/SDC_1/Documents/deploy/helao-dev/temp",
                        filename="ca.nox",
                        parseinstructions="recordsignal")),
                    meta=dict(ma=1 , substrate=1))

test_fnc(echem_sequence)

##################sequence of force
force_sequence = dict(soe= ['forceAction/read_0'],
                      params= dict(read_0= None),
                      meta=dict(ma=1 , substrate=1))

test_fnc(force_sequence)

############# sequence of pump
pump_sequence = dict(soe= ['pumping/formulation_0', 'pumping/flushSerial_0','pumping/resetPrimings_0', 
                            'pumping/getPrimings_0','pumping/refreshPrimings_0'],
                      params= dict(formulation_0= dict(comprel='[0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125]',
                                                        pumps= '[0, 1, 2, 4, 6, 7, 10, 12]',speed= 8000, totalvol=2000),
                                                        flushSerial_0=None, resetPrimings_0= None, getPrimings_0= None, refreshPrimings_0=None),
                      meta=dict(ma=2 , substrate=1))

test_fnc(pump_sequence)

#start the infinite loop
server = 'orchestrator'
action = 'infiniteLoop'
params = None
requests.post("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'] ,13380 ,server ,action), params= params).json()
