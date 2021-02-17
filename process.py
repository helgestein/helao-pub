import requests
from copy import copy
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
sys.path.append(r'../orchestrators')    

import time
from config.mischbares_small import config
import json
from copy import copy
import os
import random
import numpy as np
import matplotlib.pyplot as plt
import itertools

def test_fnc(sequence):
    server = 'orchestrator'
    action = 'addExperiment'
    params = dict(experiment=json.dumps(sequence))
    print("requesting")
    requests.post("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'] ,13380 ,server ,action),params= params).json()

substrate = 19
# real run 
x, y= np.meshgrid([5 * i for i in range(8)], [5 * i for i in range(8)])
x, y = x.flatten(), y.flatten()
pot = np.linspace(-2, -1, num=8)
cur = np.linspace((-10)**(-5), -10**(-4), num= 8)
cv_pot = np.linspace(-2, -1, num=8)
uppervort = [x+0.2 for x in cv_pot]
lowervort = [x-0.2 for x in cv_pot]
eis_pot = [i for i in np.arange(-0.2, 0.2, 0.04)]

def ca_exp(dx, dy, dz, ca_time, j , pot, substrate):
    run_sequence= dict(soe=['motor/moveWaste_0', 'minipumping/formulation_0', 'motor/RemoveDroplet_0','motor/moveSample_0', 
                        'motor/moveAbs_1','motor/moveDown_0','echem/setcurrentrange_0',
                        'echem/measure_0', 'motor/moveRel_0', 'motor/moveWaste_1'],
                        params= dict(moveWaste_0= dict(x=0, y=0, z=0),  
                                        formulation_0= dict(speed= 70, volume= 80, direction= 1), 
                                        RemoveDroplet_0= dict(x=0, y=0, z=0), 
                                        moveSample_0= dict(x=0, y=0, z=0), 
                                        moveAbs_1 = dict(dx=dx, dy=dy, dz=dz),
                                        moveDown_0 = dict(dz=0.213, steps=120, maxForce=0.44, threshold= 0.320),
                                        setcurrentrange_0= dict(crange='100uA'),
                                        measure_0= dict(procedure="ca", setpointjson= json.dumps({'applypotential': {'Setpoint value': pot}, # pot[j]
                                                    'recordsignal': {'Duration': ca_time}}),
                                                    plot="tCV",
                                                    onoffafter="off",
                                                    safepath="C:/Users/LaborRatte23-3/Documents/GitHub/helao-dev/temp",
                                                    filename="substrate_{}_ca_{}_{}.nox".format(substrate, j, ca_time),
                                                    parseinstructions='recordsignal'), 
                                    moveRel_0= dict(dx=0, dy=0, dz=-4),
                                    moveWaste_1= dict(x=0, y=0, z=0)),
                                    meta=dict(substrate=15, ma=[round(dx* 100)*10, round(dy * 100)*10],  r=0.005))
    return run_sequence


def cp_exp(dx, dy, dz, cp_time, j , cur, substrate):
    run_sequence= dict(soe=['motor/moveWaste_0', 'minipumping/formulation_0', 'motor/RemoveDroplet_0','motor/moveSample_0', 
                    'motor/moveAbs_1','motor/moveDown_0','echem/setcurrentrange_0',
                    'echem/measure_0', 'motor/moveRel_0', 'motor/moveWaste_1'],
                    params= dict(moveWaste_0= dict(x=0, y=0, z=0),  
                                    formulation_0= dict(speed= 70, volume= 80, direction= 1), 
                                    RemoveDroplet_0= dict(x=0, y=0, z=0), 
                                    moveSample_0= dict(x=0, y=0, z=0), 
                                    moveAbs_1 = dict(dx=dx, dy=dy, dz=dz),
                                    moveDown_0 = dict(dz=0.213, steps=120, maxForce=0.44, threshold= 0.320),
                                    setcurrentrange_0= dict(crange='100uA'),
                                    measure_0= dict(procedure="cp", setpointjson= json.dumps({'applycurrent': {'Setpoint value': cur}, #cur[j]
                                                'recordsignal': {'Duration': cp_time}}),
                                                plot="tCV",
                                                onoffafter="off",
                                                safepath="C:/Users/LaborRatte23-3/Documents/GitHub/helao-dev/temp",
                                                filename="substarte_{}_cp_{}_{}.nox".format(substrate, j, cp_time),
                                                parseinstructions='recordsignal'), 
                                moveRel_0= dict(dx=0, dy=0, dz=-4),
                                moveWaste_1= dict(x=0, y=0, z=0)),
                                meta=dict(substrate=15, ma=[round(dx* 100)*10, round(dy * 100)*10],  r=0.005))
    return run_sequence


def cv_exp(dx, dy, dz, uppervort, lowervort, j, substrate):
    run_sequence= dict(soe=['motor/moveWaste_0', 'minipumping/formulation_0', 'motor/RemoveDroplet_0','motor/moveSample_0', 
                        'motor/moveAbs_1','motor/moveDown_0','echem/setcurrentrange_0',
                        'echem/measure_0', 'motor/moveRel_0', 'motor/moveWaste_1'],
                        params= dict(moveWaste_0= dict(x=0, y=0, z=0),  
                                        formulation_0= dict(speed= 70, volume= 80, direction= 1), 
                                        RemoveDroplet_0= dict(x=0, y=0, z=0), 
                                        moveSample_0= dict(x=0, y=0, z=0), 
                                        moveAbs_1 = dict(dx=dx, dy=dy, dz=dz),
                                        moveDown_0 = dict(dz=0.213, steps=120, maxForce=0.44, threshold= 0.320),
                                        setcurrentrange_0= dict(crange='100uA'),
                                        measure_0= dict(procedure="cv", setpointjson= json.dumps({'FHSetSetpointPotential': {'Setpoint value': lowervort[j]+0.01}, 
                                                    'FHWait': {'Time': 2},
                                                    'CVLinearScanAdc164':{'StartValue':lowervort[j]+0.01, 'UpperVertex':uppervort[j], 'LowerVertex':lowervort[j], 'NumberOfStopCrossings':50, 'ScanRate':0.1}}),
                                                    plot="tCV",
                                                    onoffafter="off",
                                                    safepath="C:/Users/LaborRatte23-3/Documents/GitHub/helao-dev/temp",
                                                    filename="substrate_{}_cv_{}.nox".format(substrate, j),
                                                    parseinstructions='CVLinearScanAdc164'), 
                                    moveRel_0= dict(dx=0, dy=0, dz=-4),
                                    moveWaste_1= dict(x=0, y=0, z=0)),
                                    meta=dict(substrate=15, ma=[round(dx* 100)*10, round(dy * 100)*10],  r=0.005))
    return run_sequence


# plan of the experiment
all_seq = {}
time_exp = [300, 600, 900, 1200]
substrate = 19
time_exp = list(itertools.chain.from_iterable(itertools.repeat(x, 8) for x in time_exp))

for j, ca_time in zip(range(32), time_exp):
    print("{}, {}".format(x[j], y[j]))
    dx = config['lang']['safe_sample_pos'][0] + x[j]
    dy = config['lang']['safe_sample_pos'][1] + y[j]
    dz = config['lang']['safe_sample_pos'][2]
    all_seq.update({j:  ca_exp(dx, dy, dz, ca_time, j , pot[j%8], substrate)})

for j, cp_time in zip(range(32, 64, 1), time_exp):
    print("{}, {}".format(x[j], y[j]))
    dx = config['lang']['safe_sample_pos'][0] + x[j]
    dy = config['lang']['safe_sample_pos'][1] + y[j]
    dz = config['lang']['safe_sample_pos'][2]
    all_seq.update({j: cp_exp(dx, dy, dz, cp_time, j , cur[j%8], substrate)})

# Randomizing the experiment for avoiding overfitting 
random.seed(4)
random.shuffle(all_seq)

test_fnc(dict(soe=['orchestrator/start'],params={'start':None},meta=dict(substrate=15, ma=[config['lang']['safe_sample_pos'][0], config['lang']['safe_sample_pos'][1]], r=0.005)))

test_fnc(run_sequence)

test_fnc(dict(soe=['orchestrator/finish'],params={'finish':None},meta=dict(substrate=15, ma=[config['lang']['safe_sample_pos'][0], config['lang']['safe_sample_pos'][1]], r=1)))



