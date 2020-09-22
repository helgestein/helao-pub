import requests
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
sys.path.append(r'../orchestrators')

import time
from config.mischbares_small import config
import json
from copy import copy

import numpy as np
import matplotlib.pyplot as plt


def test_fnc(sequence):
    server = 'orchestrator'
    action = 'addExperiment'
    params = dict(experiment=json.dumps(sequence))
    requests.post("http://{}:{}/{}/{}".format(
    config['servers']['orchestrator']['host'] ,13380 ,server ,action),
    params= params).json()



#################sequesnce of the lang_motor action
lang_sequence= dict(soe=['motor/getPos_0', 'motor/moveRel_0', 'motor/moveAbs_0',
                         'motor/moveHome_0','motor/moveWaste_0', 'motor/getPos_1', 'motor/moveDown_0'], 
                    params= dict(getPos_0 = None, moveRel_0= dict(dx=-10, dy=-10, dz=50),
                                moveAbs_0= dict(dx=0, dy=0, dz=0), moveHome_0= None,
                                moveWaste_0= None, getPos_1= None, moveDown_0= dict(dz=1, steps=10, maxForce=0.1),
                    meta=dict(ma=1 , substrate=1))

test_fnc(lang_sequence)

lang_sequence= dict(soe=['motor/moveDown_0'], 
                    params= dict(moveDown_0= dict(dz=10,steps=5,maxForce=0.1)),
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

##########################
#test all instruments at once
dry_run_sequence_1= dict(soe=['motor/moveHome_0', 'motor/getPos_0', 'motor/moveAbs_0', 
                    'pumping/formulation_0', 'forceAction/read_0', 'motor/getPos_1',
                    'motor/moveDown_0', 'echem/measure_0', 'motor/moveWaste_0', 'motor/moveHome_1'],
                    params= dict(moveHome_0= None, getPos_0= None, moveAbs_0= dict(dx=65, dy=85, dz=5), 
                    formulation_0= dict(comprel='[0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125]',
                    pumps= '[0, 1, 2, 4, 6, 7, 10, 12]',speed= 8000, totalvol=2000), read_0= None, 
                    getPos_1= None, moveDown_0= dict(dz=1, steps=10, maxForce=0.1), 
                    measure_0= dict(procedure="ca", setpointjson="{'applypotential': {'Setpoint value': 0.01}, 'recordsignal': {'Duration': 10}}",
                        plot="tCV",
                        onoffafter="off",
                        safepath="C:/Users/SDC_1/Documents/deploy/helao-dev/temp",
                        filename="ca.nox",
                        parseinstructions="recordsignal"), moveWaste_0= None, moveHome_1= None),
                meta=dict(ma=1 , substrate=1))

dry_run_sequence_2= dict(soe=['motor/moveHome_0', 'motor/getPos_0', 'motor/moveAbs_0', 
                    'pumping/formulation_0', 'forceAction/read_0', 'motor/getPos_1',
                    'motor/moveDown_0', 'echem/measure_0', 'motor/moveWaste_0', 'motor/moveHome_1'],
                    params= dict(moveHome_0= None, getPos_0= None, moveAbs_0= dict(dx=70, dy=80, dz=4), 
                    formulation_0= dict(comprel='[0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125]',
                    pumps= '[0, 1, 2, 4, 6, 7, 10, 12]',speed= 8000, totalvol=2000), read_0= None, 
                    getPos_1= None, moveDown_0= dict(dz=2, steps=20, maxForce=0.1), 
                    measure_0= dict(procedure="ca", setpointjson="{'applypotential': {'Setpoint value': 0.01}, 'recordsignal': {'Duration': 10}}",
                        plot="tCV",
                        onoffafter="off",
                        safepath="C:/Users/SDC_1/Documents/deploy/helao-dev/temp",
                        filename="ca.nox",
                        parseinstructions="recordsignal"), moveWaste_0= None, moveHome_1= None),
                meta=dict(ma=1 , substrate=2))

test_fnc(dry_run_sequence_1)
test_fnc(dry_run_sequence_2)
################################

x, y = np.meshgrid([4 * i for i in range(8)], [4 * i for i in range(8)])
x, y = x.flatten(), y.flatten()

for j in range(64):
    print("{}, {}".format(x[j], y[j]))
    dx = config['lang']['safe_sample_pos'][0] + x[j]
    dy = config['lang']['safe_sample_pos'][1] + y[j]
    dz = config['lang']['safe_sample_pos'][2]
    run_sequence= dict(soe=['motor/moveWaste_0', 'pumping/formulation_0', 'motor/RemoveDroplet_0', 'motor/moveSample_0', 
                        'motor/moveAbs_0','motor/moveDown_0','motor/moveDown_0', 
                        'echem/measure_0', 'pumping/formulation_1', 'motor/moveHome_0'],
                        params= dict(moveWaste_0= None,  
                        formulation_0= dict(comprel='[0.125]',
                        pumps= '[0]',speed= 400, totalvol=100, direction=1), RemoveDroplet_0= None, moveSample_0= None, 
                        moveAbs_0 = dict(dx=dx, dy=dy, dz=dz),
                        moveDown_0 = dict(dz=0.45, steps=10, maxForce=0.1),
                        measure_0= dict(procedure="ca", setpointjson="{'applypotential': {'Setpoint value': 0.01}, 'recordsignal': {'Duration': 10}}",
                            plot="tCV",
                            onoffafter="off",
                            safepath="C:/Users/SDC_1/Documents/deploy/helao-dev/temp",
                            filename="ca_{}.nox".format(j),
                            parseinstructions="recordsignal"), 
                            formulation_1= dict(comprel='[0.125]', pumps= '[0]',speed= 400, totalvol=50, direction=0),
                            moveHome_0= None),
                    meta=dict(ma=1 , substrate=j))
    test_fnc(run_sequence)

###############################
#start the infinite loop
server = 'orchestrator'
action = 'infiniteLoop'
params = None
requests.post("http://{}:{}/{}/{}".format(
    config['servers']['orchestrator']['host'] ,13380 ,server ,action),
    params= params).json()
