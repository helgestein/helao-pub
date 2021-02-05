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

import numpy as np
import matplotlib.pyplot as plt


def test_fnc(sequence):
    server = 'orchestrator'
    action = 'addExperiment'
    params = dict(experiment=json.dumps(sequence))
    requests.post("http://{}:{}/{}/{}".format(
    config['servers']['orchestrator']['host'] ,13380 ,server ,action),
    params= params).json()

# real run 
x, y= np.meshgrid([4 * i for i in range(4)], [3 * i for i in range(12)])
x, y = x.flatten(), y.flatten()
pot = np.linspace(-1, 2, num=72)
cur = np.linspace((-10)**(-5), 10**(-5), num= 72)
uppervort = [x+0.5 for x in pot]
lowervort = [x-0.5 for x in pot]
eis_pot = [i for i in np.arange(-0.2, 0.2, 0.04)]

# plan of the experiment 
# pot[j]
all_seq = []
test_fnc(dict(soe=['orchestrator/start'],params={'start':None},meta=dict(substrate=11, ma=[config['lang']['safe_sample_pos'][0], config['lang']['safe_sample_pos'][1]], r=1)))
for j in range(48):
    print("{}, {}".format(x[j], y[j]))
    dx = config['lang']['safe_sample_pos'][0] + x[j]
    dy = config['lang']['safe_sample_pos'][1] + y[j]
    dz = config['lang']['safe_sample_pos'][2]
    

    run_sequence= dict(soe=['motor/moveWaste_0', 'minipumping/formulation_0', 'motor/RemoveDroplet_0','motor/moveSample_0', 
                        'motor/moveAbs_1','motor/moveDown_0','echem/setcurrentrange_0',
                        'echem/measure_0', 'motor/moveRel_0', 'motor/moveWaste_1'],
                        params= dict(moveWaste_0= dict(x=0, y=0, z=0),  
                                        formulation_0= dict(speed= 70, volume= 180, direction= 1), 
                                        RemoveDroplet_0= dict(x=0, y=0, z=0), 
                                        moveSample_0= dict(x=0, y=0, z=0), 
                                        moveAbs_1 = dict(dx=dx, dy=dy, dz=dz),
                                        moveDown_0 = dict(dz=0.170, steps=80, maxForce=0.44, threshold= 0.172),
                                        setcurrentrange_0= dict(crange='100uA'),
                                        measure_0= dict(procedure="cv", setpointjson= json.dumps({'FHSetSetpointPotential': {'Setpoint value': 0.4}, 
                                                    'FHWait': {'Time': 2},
                                                    'CVLinearScanAdc164':{'StartValue':0.4, 'UpperVertex':1.5, 'LowerVertex':0.399, 'NumberOfStopCrossings':1, 'ScanRate':0.1}}),
                                                    plot="tCV",
                                                    onoffafter="off",
                                                    safepath="C:/Users/LaborRatte23-3/Documents/helao-dev/temp",
                                                    filename="cv_{}.nox".format(j),
                                                    parseinstructions='CVLinearScanAdc164'), 
                                    moveRel_0= dict(dx=0, dy=0, dz=-4),
                                    moveWaste_1= dict(x=0, y=0, z=0)),
                                    meta=dict(substrate=11, ma=[round(dx* 100)*10, round(dy * 100)*10],  r=1))    

    test_fnc(run_sequence)

test_fnc(dict(soe=['orchestrator/finish'],params={'finish':None},meta=dict(substrate=11, ma=[config['lang']['safe_sample_pos'][0], config['lang']['safe_sample_pos'][1]], r=1)))






