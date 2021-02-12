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
    print("requesting")
    requests.post("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'] ,13380 ,server ,action),params= params).json()

# real run 
x, y= np.meshgrid([6 * i for i in range(6)], [6 * i for i in range(6)])
x, y = x.flatten(), y.flatten()
pot = np.linspace(-2, -1, num=6)
cur = np.linspace((-10)**(-5), -10**(-4), num= 6)
cv_pot = np.linspace(-2, -1, num=5)
uppervort = [x+0.2 for x in cv_pot]
lowervort = [x-0.2 for x in cv_pot]
eis_pot = [i for i in np.arange(-0.2, 0.2, 0.04)]

# plan of the experiment 
# pot[j]
all_seq = []
test_fnc(dict(soe=['orchestrator/start'],params={'start':None},meta=dict(substrate=15, ma=[config['lang']['safe_sample_pos'][0], config['lang']['safe_sample_pos'][1]], r=0.005)))

for j in range(36):
    print("{}, {}".format(x[j], y[j]))
    dx = config['lang']['safe_sample_pos'][0] + x[j]
    dy = config['lang']['safe_sample_pos'][1] + y[j]
    dz = config['lang']['safe_sample_pos'][2]
    
    if j < 6:

        # ca run 
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
                                            measure_0= dict(procedure="ca", setpointjson= json.dumps({'applypotential': {'Setpoint value': pot[j]}, 
                                                        'recordsignal': {'Duration': 900}}),
                                                        plot="tCV",
                                                        onoffafter="off",
                                                        safepath="C:/Users/LaborRatte23-3/Documents/GitHub/helao-dev/temp",
                                                        filename="ca_{}.nox".format(j),
                                                        parseinstructions='recordsignal'), 
                                        moveRel_0= dict(dx=0, dy=0, dz=-4),
                                        moveWaste_1= dict(x=0, y=0, z=0)),
                                        meta=dict(substrate=15, ma=[round(dx* 100)*10, round(dy * 100)*10],  r=0.005))    
    if 5 < j < 12:
        #cp run 
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
                                            measure_0= dict(procedure="cp", setpointjson= json.dumps({'applycurrent': {'Setpoint value': cur[j%6]}, 
                                                        'recordsignal': {'Duration': 900}}),
                                                        plot="tCV",
                                                        onoffafter="off",
                                                        safepath="C:/Users/LaborRatte23-3/Documents/GitHub/helao-dev/temp",
                                                        filename="cp_{}.nox".format(j),
                                                        parseinstructions='recordsignal'), 
                                        moveRel_0= dict(dx=0, dy=0, dz=-4),
                                        moveWaste_1= dict(x=0, y=0, z=0)),
                                        meta=dict(substrate=15, ma=[round(dx* 100)*10, round(dy * 100)*10],  r=0.005))    
    
    if 11 < j < 17:
        #cv run 
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
                                            measure_0= dict(procedure="cv", setpointjson= json.dumps({'FHSetSetpointPotential': {'Setpoint value': lowervort[j%6]+0.01}, 
                                                        'FHWait': {'Time': 2},
                                                        'CVLinearScanAdc164':{'StartValue':lowervort[j%6]+0.01, 'UpperVertex':uppervort[j%6], 'LowerVertex':lowervort[j%6], 'NumberOfStopCrossings':50, 'ScanRate':0.1}}),
                                                        plot="tCV",
                                                        onoffafter="off",
                                                        safepath="C:/Users/LaborRatte23-3/Documents/GitHub/helao-dev/temp",
                                                        filename="cv_{}.nox".format(j),
                                                        parseinstructions='CVLinearScanAdc164'), 
                                        moveRel_0= dict(dx=0, dy=0, dz=-4),
                                        moveWaste_1= dict(x=0, y=0, z=0)),
                                        meta=dict(substrate=15, ma=[round(dx* 100)*10, round(dy * 100)*10],  r=0.005))   
    if j == 17:
        # long cv run
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
                                            measure_0= dict(procedure="cv", setpointjson= json.dumps({'FHSetSetpointPotential': {'Setpoint value': -2}, 
                                                        'FHWait': {'Time': 2},
                                                        'CVLinearScanAdc164':{'StartValue':-2, 'UpperVertex':1.2, 'LowerVertex':-2.1, 'NumberOfStopCrossings':50, 'ScanRate':0.1}}),
                                                        plot="tCV",
                                                        onoffafter="off",
                                                        safepath="C:/Users/LaborRatte23-3/Documents/GitHub/helao-dev/temp",
                                                        filename="cv_{}.nox".format(j),
                                                        parseinstructions='CVLinearScanAdc164'), 
                                        moveRel_0= dict(dx=0, dy=0, dz=-4),
                                        moveWaste_1= dict(x=0, y=0, z=0)),
                                        meta=dict(substrate=15, ma=[round(dx* 100)*10, round(dy * 100)*10],  r=0.005))     
    if 17 < j < 24:
        #ca run on copper
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
                                            measure_0= dict(procedure="ca", setpointjson= json.dumps({'applypotential': {'Setpoint value': pot[j%6]}, 
                                                        'recordsignal': {'Duration': 900}}),
                                                        plot="tCV",
                                                        onoffafter="off",
                                                        safepath="C:/Users/LaborRatte23-3/Documents/GitHub/helao-dev/temp",
                                                        filename="ca_{}.nox".format(j),
                                                        parseinstructions='recordsignal'), 
                                        moveRel_0= dict(dx=0, dy=0, dz=-4),
                                        moveWaste_1= dict(x=0, y=0, z=0)),
                                        meta=dict(substrate=15, ma=[round(dx* 100)*10, round(dy * 100)*10],  r=0.005))    
    if 23 < j < 30:
        #cp run on copper
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
                                            measure_0= dict(procedure="cp", setpointjson= json.dumps({'applycurrent': {'Setpoint value': cur[j%6]}, 
                                                        'recordsignal': {'Duration': 900}}),
                                                        plot="tCV",
                                                        onoffafter="off",
                                                        safepath="C:/Users/LaborRatte23-3/Documents/GitHub/helao-dev/temp",
                                                        filename="cp_{}.nox".format(j),
                                                        parseinstructions='recordsignal'), 
                                        moveRel_0= dict(dx=0, dy=0, dz=-4),
                                        moveWaste_1= dict(x=0, y=0, z=0)),
                                        meta=dict(substrate=15, ma=[round(dx* 100)*10, round(dy * 100)*10],  r=0.005))
    if 29 < j < 35:
        #cv run on copper
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
                                            measure_0= dict(procedure="cv", setpointjson= json.dumps({'FHSetSetpointPotential': {'Setpoint value': lowervort[j%6]+0.01}, 
                                                        'FHWait': {'Time': 2},
                                                        'CVLinearScanAdc164':{'StartValue':lowervort[j%6]+0.01, 'UpperVertex':uppervort[j%6], 'LowerVertex':lowervort[j%6], 'NumberOfStopCrossings':50, 'ScanRate':0.1}}),
                                                        plot="tCV",
                                                        onoffafter="off",
                                                        safepath="C:/Users/LaborRatte23-3/Documents/GitHub/helao-dev/temp",
                                                        filename="cv_{}.nox".format(j),
                                                        parseinstructions='CVLinearScanAdc164'), 
                                        moveRel_0= dict(dx=0, dy=0, dz=-4),
                                        moveWaste_1= dict(x=0, y=0, z=0)),
                                        meta=dict(substrate=15, ma=[round(dx* 100)*10, round(dy * 100)*10],  r=0.005))    
    else: 
        #long cv run on copper 
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
                                            measure_0= dict(procedure="cv", setpointjson= json.dumps({'FHSetSetpointPotential': {'Setpoint value': -2}, 
                                                        'FHWait': {'Time': 2},
                                                        'CVLinearScanAdc164':{'StartValue':-2, 'UpperVertex':1.2, 'LowerVertex':-2.1, 'NumberOfStopCrossings':50, 'ScanRate':0.1}}),
                                                        plot="tCV",
                                                        onoffafter="off",
                                                        safepath="C:/Users/LaborRatte23-3/Documents/GitHub/helao-dev/temp",
                                                        filename="cv_{}.nox".format(j),
                                                        parseinstructions='CVLinearScanAdc164'), 
                                        moveRel_0= dict(dx=0, dy=0, dz=-4),
                                        moveWaste_1= dict(x=0, y=0, z=0)),
                                        meta=dict(substrate=15, ma=[round(dx* 100)*10, round(dy * 100)*10],  r=0.005))    


    test_fnc(run_sequence)

test_fnc(dict(soe=['orchestrator/finish'],params={'finish':None},meta=dict(substrate=15, ma=[config['lang']['safe_sample_pos'][0], config['lang']['safe_sample_pos'][1]], r=1)))






