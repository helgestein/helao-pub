import numpy as np 
import itertools as it 
import requests
import json
import random
import sys
import time
sys.path.append(r'../config')
sys.path.append('config')
from sdc_4 import config

import os
import datetime

### path: 'safepath':'C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp'

def test_fnc(sequence,thread=0):
    server = 'orchestrator'
    action = 'addExperiment'
    params = dict(experiment=json.dumps(sequence),thread=thread)
    print("requesting")
    req_res = requests.post("http://{}:{}/{}/{}".format(
        config['servers']['orchestrator']['host'], 13380, server, action), params=params).json()
    return req_res
'''
substrate = 59
x, y = np.meshgrid([2.6*i for i in range(12)], [2.6*i for i in range(12)])
x, y = x.flatten(), y.flatten()




n = 134  
initial_down_height = 12
step_size = 0.060 
num_steps= 81
max_force = 10
threshold_step = 0.061



test_fnc(dict(soe=['orchestrator/start'], params={'start':{'collectionkey' : 'substrate_{}'.format(substrate)}}, meta=dict()))

for i in range(n):
    dx = config['lang']['safe_sample_pos'][0] + x[0]
    dy = config['lang']['safe_sample_pos'][1] + y[1]
    dz = config['lang']['safe_sample_pos'][2]
  
    sequence_run = dict(soe=[f'lang/moveWaste_{2*i}', f'pump/formulation_{i}', f'lang/RemoveDroplet_{i}',f'lang/moveSample_{i}',f'lang/moveAbs_{i}',
                       f'lang/moveRel_{2*i}',f'lang/moveDown_{i}', f'autolab/setcurrentrange_{i}', 
                       f'autolab/measure_{i}', f'lang/moveRel_{2*i+1}',f'lang/moveWaste_{2*i+1}'], 
                       params={f'moveWaste_{2*i}':{'x': 0, 'y':0, 'z':0},
                            f'formulation_{2*i}': {'comprel' : "[0.5, 0.5]", 'pumps': "[0, 2]", 'speed': 1500, 'totalvol': 350, 'direction':1},
                            f'RemoveDroplet_{i}': {'x':0, 'y':0, 'z':0},
                            f'moveSample_{i}': {'x':0, 'y':0, 'z':0},
                            f'moveAbs_{i}': {'dx':dx, 'dy':dy, 'dz':dz},
                            f'moveRel_{2*i}': {'dx':0, 'dy':0, 'dz':9}, 
                            f'moveDown_{i}': {'dz':0.09, 'steps':20, 'maxForce':2.6, 'threshold': 0.1},
                            f'setcurrentrange_{i}': dict(crange='100uA'),
                            f'measure_{i}': {'procedure': 'ca', 'setpointjson': json.dumps({'applypotential': {'Setpoint value': -1},
                                                'recordsignal': {'Duration': 300}}),
                                                'plot':'tCV',
                                                'onoffafter':'off',
                                                'safepath':'C:/Users/LaborRatte23-3/Documents/GitHub/helao-dev/temp',
                                                'filename':'substrate_{}_ca_{}.nox'.format(substrate, i),
                                                'parseinstructions':'recordsignal'},
                            f'moveRel_{2*i+1}':{'dx':0, 'dy':0, 'dz':-5},
                            f'moveWaste_{2*i+1}': {'x':0, 'y': 0, 'z':0}}, 
                        meta=dict())
    test_fnc(soe)
test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))
'''

substrate = 999

test_fnc(dict(soe=['orchestrator/start'], params={'start':{'collectionkey' : 'substrate_{}'.format(substrate)}}, meta=dict()))
for i in range(2):
    print(f'exp:{i}')
    sequence_run = dict(soe=[f'lang/moveWaste_{i}', f'minipump/formulation_{i}', f'lang/RemoveDroplet_{i}', f'lang/moveSample_{i}'],
	                        params={f'moveWaste_{i}':{'x': 0, 'y':0, 'z':0},
                            f'formulation_{i}': {'speed': 80, 'volume': 250, 'direction': 1},
                            f'RemoveDroplet_{i}': {'x':0, 'y':0, 'z':0},
                            f'moveSample_{i}': {'x':0, 'y':0, 'z':0}},
                        meta=dict())
    test_fnc(sequence_run)
    time.sleep(60)
    print('Test number', i)
test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))


### Sequencial potential shift determination

x = np.arange(20., 50., 5.)
y = np.ones(len(x)) * 30
t = 30
substrate = 999

test_fnc(dict(soe=['orchestrator/start'], params={'start':{'collectionkey' : 'substrate_{}'.format(substrate)}}, meta=dict()))

print('Sequencial cycling voltammetry with ferrocene')

for i in range(len(x)):
    dx = config['lang']['safe_sample_pos'][0] + x[0]
    dy = config['lang']['safe_sample_pos'][1] + y[1]
    dz = config['lang']['safe_sample_pos'][2]
  
    sequence_run = dict(soe=[f'lang/moveWaste_{2*i}', f'pump/formulation_{i}', f'lang/RemoveDroplet_{i}',f'lang/moveSample_{i}',f'lang/moveAbs_{i}',
                       f'lang/moveRel_{2*i}',f'lang/moveDown_{i}', f'autolab/setcurrentrange_{i}', f'autolab/potential_{i}',
                       f'autolab/measure_{i}', f'lang/moveWaste_{2*i+1}'], 
                       params={f'moveWaste_{2*i}':{'x': 0, 'y':0, 'z':0},
                            f'formulation_{2*i}': {'comprel' : "[0.5, 0.5]", 'pumps': "[0, 2]", 'speed': 1500, 'totalvol': 350, 'direction':1},
                            f'RemoveDroplet_{i}': {'x':0, 'y':0, 'z':0},
                            f'moveSample_{i}': {'x':0, 'y':0, 'z':0},
                            f'moveAbs_{i}': {'dx':dx, 'dy':dy, 'dz':dz},
                            f'moveRel_{2*i}': {'dx':0, 'dy':0, 'dz':9}, 
                            f'moveDown_{i}': {'dz':0.049, 'steps':269, 'maxForce':0.89, 'threshold': 0.09},
                            f'setcurrentrange_{i}': dict(crange='100uA'),
                            f'potential_{i}': None,
                            f'measure_{i}': {'procedure': 'cv', 'setpointjson': json.dumps({'FHSetSetpointPotential': {'Setpoint value': -0.200},
                                                'FHWait': {'Time': 10},
                                                'CVLinearScanAdc164': {'StartValue': -0.200, 'UpperVertex': 0.5, 'LowerVertex':-0.5, 'NumberOfStopCrossings': 6, 'Step': 0.002, 'ScanRate': 0.010}}),
                                                'plot':'tCV',
                                                'onoffafter':'off',
                                                'safepath':'C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp',
                                                'filename':'substrate_{}_cv_{}.nox'.format(substrate, i),
                                                'parseinstructions':'CVLinearScanAdc164'},
                            f'moveWaste_{2*i+1}': {'x':0, 'y': 0, 'z':0}}, 
                        meta=dict())
                        
    ### wrute the second measure 
    ret = test_fnc(sequence_run)
    #time.sleep(t)
test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))


#################################

### OCP + EIS ideal
'''
substrate = 999
test_fnc(dict(soe=['orchestrator/start'], params={'start':{'collectionkey' : 'substrate_{}'.format(substrate)}}, meta=dict()))
for i in range(3):
    print(f'exp:{i}')
    ocp = dict(soe=[f'autolab/measure_{i}'],
	                        params={f'measure_{i}':{'procedure': 'ocp_rs', 'setpointjson': json.dumps({'recordsignal': {'Duration': 30}}),
                                                            'plot': "tCV",
                                                            'onoffafter': "off",
                                                            'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                                            'filename': 'substrate_{}_ocp_rs_{}.nox'.format(substrate, i),
                                                            'parseinstructions':'recordsignal'}},
                        meta=dict())
    ocp_data = test_fnc(ocp)
    time.sleep(35)
    ocp_pot = ocp_data['recordsignal']['WE(1).Potential'][-1]
    print(f'OCP potential is {ocp_pot} V')
    eis = dict(soe=[f'autolab/measure_{i}'],
	                        params={f'measure_{i}':{'procedure': 'eis', 'setpointjson': json.dumps({'FHSetSetpointPotential': {'Setpoint value': ocp_pot}}),
                                                            'plot': "impedance",
                                                            'onoffafter': "off",
                                                            'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                                            'filename': 'substrate_{}_eis_{}.nox'.format(substrate, i),
                                                            'parseinstructions':'FIAMeasPotentiostatic'}},
                        meta=dict())
    test_fnc(eis)
test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))
'''

### OCP + EIS function with json recall

substrate = 999
test_fnc(dict(soe=['orchestrator/start'], params={'start':{'collectionkey' : 'substrate_{}'.format(substrate)}}, meta=dict()))
for j in range(1):
    i = 11+j

    ocp = dict(soe=[f'autolab/measure_{i}'],
	                        params={f'measure_{i}':{'procedure': 'ocp_rs', 'setpointjson': json.dumps({'recordsignal': {'Duration': 20, 'Interval time in µs': 1}}),
                                                            'plot': "tCV",
                                                            'onoffafter': "off",
                                                            'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                                            'filename': 'substrate_{}_ocp_rs_{}.nox'.format(substrate, i),
                                                            'parseinstructions':'recordsignal'}},
                        meta=dict())
    test_fnc(ocp)
    time.sleep(30)
    path = r"C:\Users\LaborRatte23-2\Documents\GitHub\helao-dev_2\temp"
    fn = 'substrate_{}_ocp_rs_{}_data.json'.format(substrate, i)
    ocp_data = json.load(open(os.path.join(path,fn),'r'))
    ocp_pot = np.mean(ocp_data['recordsignal']['WE(1).Potential'][-5:])
    print(f'OCP potential is {ocp_pot} V')
    eis = dict(soe=[f'autolab/measure_{i}'],
	                        params={f'measure_{i}':{'procedure': 'eis', 'setpointjson': json.dumps({'FHSetSetpointPotential': {'Setpoint value': ocp_pot}}),
                                                            'plot': "impedance",
                                                            'onoffafter': "off",
                                                            'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                                            'filename': 'substrate_{}_eis_{}.nox'.format(substrate, i),
                                                            'parseinstructions':'FIAMeasPotentiostatic'}},
                        meta=dict())
    test_fnc(eis)
    time.sleep(90)
    print(f'exp:{i} is finished')
test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))

### OCP + CV json recall
x0 = np.arange(25., 50., 5.)
x1 = np.arange(5., 50., 5.)
x = np.concatenate((x0, x1), axis=0)
y0 = np.ones(len(x0)) * 30
y1 = np.ones(len(x1)) * 35
y = np.concatenate((y0, y1), axis=0)
substrate = 999
test_fnc(dict(soe=['orchestrator/start'], params={'start':{'collectionkey' : 'substrate_{}'.format(substrate)}}, meta=dict()))
for j in range(len(x)):
    i = 100+j
    dx = x[j]
    dy = y[j]
    dz = config['lang']['safe_sample_pos'][2]
    print(f'exp:{j}/{len(x)-1} is started, time: {str(datetime.datetime.now())}')
    sequence_run = dict(soe=[f'lang/moveWaste_{i}', f'minipump/formulation_{i}', f'lang/RemoveDroplet_{i}',f'lang/moveSample_{i}', f'lang/moveDown_{i}'], 
                       params={f'moveWaste_{i}':{'x': 0, 'y':0, 'z':0},
                            f'formulation_{i}': {'speed': 50, 'volume': 500, 'direction': 1},
                            f'RemoveDroplet_{i}': {'x':0, 'y':0, 'z':0},
                            f'moveSample_{i}': {'x':dx, 'y':dy, 'z':dz}, 
                            f'moveDown_{i}': {'dz':0.049, 'steps':269, 'maxForce':0.89, 'threshold': 0.09}}, 
                        meta=dict())
    test_fnc(sequence_run)                   
    time.sleep(120)
    ocp = dict(soe=[f'autolab/measure_{i}'],
	                        params={f'measure_{i}':{'procedure': 'ocp_rs', 'setpointjson': json.dumps({'recordsignal': {'Duration': 60, 'Interval time in µs': 1}}),
                                                            'plot': "tCV",
                                                            'onoffafter': "off",
                                                            'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                                            'filename': 'substrate_{}_ocp_rs_{}.nox'.format(substrate, i),
                                                            'parseinstructions':'recordsignal'}},
                        meta=dict())
    test_fnc(ocp)
    time.sleep(75)
    path = r"C:\Users\LaborRatte23-2\Documents\GitHub\helao-dev_2\temp"
    fn = 'substrate_{}_ocp_rs_{}_data.json'.format(substrate, i)
    ocp_data = json.load(open(os.path.join(path,fn),'r'))
    ocp_pot = np.mean(ocp_data['recordsignal']['WE(1).Potential'][-5:])
    print(f'OCP potential is {ocp_pot} V')
    cv = dict(soe=[f'autolab/measure_{i}'],
	                        params={f'measure_{i}':{'procedure': 'cv_fc', 'setpointjson': json.dumps({
                                                'FHSetSetpointPotential': {'Setpoint value': ocp_pot},
                                                'FHWait': {'Time': 5},
                                                'FHCyclicVoltammetry2': {'Start value': ocp_pot, 'Upper vertex': 0.750, 'Lower vertex':-0.500, 'NrOfStopCrossings': 20, 'Step': 0.002, 'Scanrate': 0.010}}),
                                                            'plot': "tCV",
                                                            'onoffafter': "off",
                                                            'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                                            'filename': 'substrate_{}_cv_fc_{}.nox'.format(substrate, i),
                                                            'parseinstructions':'FHCyclicVoltammetry2'}},
                        meta=dict())
    test_fnc(cv)
    time.sleep(1.25/0.01*20+200)
    print(f'exp:{j}/{len(x)-1} is finished, time: {str(datetime.datetime.now())}')
test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))

xx = np.arange(5, 50, 5)
yy = np.arange(5, 50, 5)
x, y = np.meshgrid(xx, yy)

### Testing the new method for droplet removal (using second SDC tip)
#

#yy = np.arange(25, 35, 5)
#x, y = np.meshgrid(xx, yy)
#x = x.flatten()
#y = y.flatten()
#x = [22.5]
#y = [7.5]
x = np.arange(7.5, 47.5, 5)
y = 42.5*np.ones(len(x))
substrate = 0
test_fnc(dict(soe=['orchestrator/start'], params={'start':{'collectionkey' : 'substrate_{}'.format(substrate)}}, meta=dict()))
for i in range(len(x)):
    dx = x[i]
    dy = y[i]
    dz = config['lang']['safe_sample_pos'][2]
    sequence_1 = dict(soe=[f'lang/moveWaste_{10*i}', f'hamilton/pumpL_{10*i}',f'hamilton/pumpR_{10*i}', f'hamilton/pumpL_{10*i+1}', f'lang/moveWaste_{10*i+1}',f'hamilton/pumpR_{10*i+1}'], 
                       params={f'moveWaste_{10*i}':{'x': -25, 'y':0, 'z':0},
                            f'pumpL_{10*i}': {'volume': 300, 'times': 1},
                            f'pumpR_{10*i}': {'volume': 200, 'times': 1},
                            f'pumpL_{10*i+1}': {'volume': -200, 'times': 1},
                            f'moveWaste_{10*i+1}':{'x': -12.6, 'y':-4.3, 'z':8.8},
                            f'pumpR_{10*i+1}': {'volume': 200, 'times': 1}}, 
                        meta=dict())
    sequence_2 = dict(soe=[f'lang/moveWaste_{10*i+2}', f'lang/RemoveDroplet_{10*i}', f'lang/moveSample_{10*i}', f'lang/moveDown_{10*i}', f'hamilton/pumpL_{10*i+2}', f'hamilton/pumpR_{10*i+2}'], 
                       params={f'moveWaste_{10*i+2}':{'x': -25, 'y':0, 'z':0},
                            f'RemoveDroplet_{10*i}': {'x':-25, 'y':0, 'z':0},
                            f'moveSample_{10*i}': {'x':dx, 'y':dy, 'z':dz}, 
                            f'moveDown_{10*i}': {'dz':0.049, 'steps':260, 'maxForce':3, 'threshold': 0.09},
                            f'pumpL_{10*i+2}': {'volume': 100, 'times': 1},
                            f'pumpR_{10*i+2}': {'volume': 200, 'times': 10}}, 
                        meta=dict())
    sequence_3 = dict(soe=[f'hamilton/pumpL_{10*i+2}',f'lang/moveAbs_{10*i}',f'hamilton/pumpL_{10*i+3}',f'lang/moveWaste_{10*i+3}'], 
                       params={f'pumpL_{10*i+2}': {'volume': -200, 'times': 1},
                            f'moveAbs_{10*i}': {'x':dx, 'y':dy, 'z':-0.2},
                            f'pumpL_{10*i+3}': {'volume': -200, 'times': 1},
                        	f'moveWaste_{10*i+3}':{'x': -25, 'y':0, 'z':0}},
                        meta=dict())                                         
    test_fnc(sequence_1)
    print(f'exp: {i}/{len(x)-1} is running, time: {str(datetime.datetime.now())}')
    time.sleep(60)
    test_fnc(sequence_2)
    time.sleep(900)
    test_fnc(sequence_3)
    time.sleep(60)
test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))
#

### Testing the new method for droplet removal (dry-wet-dry method)
xx = np.arange(7.5, 47.5, 5)
yy = np.arange(27.5, 37.5, 5)
x, y = np.meshgrid(xx, yy)
x = x.flatten()
y = y.flatten()
substrate = 0
test_fnc(dict(soe=['orchestrator/start'], params={'start':{'collectionkey' : 'substrate_{}'.format(substrate)}}, meta=dict()))
for i in range(len(x)):

    dx = x[i]
    dy = y[i]
    dz = config['lang']['safe_sample_pos'][2]
    sequence_run_1 = dict(soe=[f'lang/moveWaste_{2*i}', f'hamilton/pumpL_{5*i}', f'hamilton/pumpL_{5*i+1}',f'lang/RemoveDroplet_{i}', f'lang/moveSample_{i}', f'lang/moveDown_{i}', f'hamilton/pumpL_{5*i+2}'], 
                       params={f'moveWaste_{2*i}':{'x': -25, 'y':0, 'z':0},
                            f'pumpL_{5*i}': {'volume': 250, 'times': 1},
                            f'pumpL_{5*i+1}': {'volume': -250, 'times': 1},
                            f'RemoveDroplet_{i}': {'x':-25, 'y':0, 'z':0},
                            f'moveSample_{i}': {'x':dx, 'y':dy, 'z':dz}, 
                            f'moveDown_{i}': {'dz':0.049, 'steps':260, 'maxForce':2.5, 'threshold': 0.09},
                            f'pumpL_{5*i+2}': {'volume': 350, 'times': 1}}, 
                        meta=dict())
    test_fnc(sequence_run_1)
    time.sleep(180)
    sequence_run_2 = dict(soe=[f'hamilton/pumpL_{5*i+3}', f'lang/moveWaste_{2*i+1}', f'hamilton/pumpL_{5*i+4}'], 
                       params={f'pumpL_{5*i+3}': {'volume': -350, 'times': 1},
                            f'moveWaste_{2*i+1}':{'x': -25, 'y':0, 'z':0},
                            f'pumpL_{5*i+4}': {'volume': 350, 'times': 1}},
                        meta=dict())
    test_fnc(sequence_run_2)
    print(f'exp:{i}/{len(x)-1} is finished, time: {str(datetime.datetime.now())}')
test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))

### Testing pumping (hamilton)
substrate=0
test_fnc(dict(soe=['orchestrator/start'], params={'start':{'collectionkey' : 'substrate_{}'.format(substrate)}}, meta=dict()))
hamilton_sequence = dict(soe= ['hamilton/pumpL_0'],
                      params= {f'pumpL_0': {'volume': 250, 'times': 1}},
                        meta=dict())
test_fnc(hamilton_sequence)
test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))

# lang fast test
substrate=0
test_fnc(dict(soe=['orchestrator/start'], params={'start':{'collectionkey' : 'substrate_{}'.format(substrate)}}, meta=dict()))
lang_sequence = dict(soe=[f'lang/moveWaste_0', 'lang/moveWaste_1'], 
                       params={f'moveWaste_0':{'x': 0, 'y':0, 'z':0},
                            f'moveWaste_1':{'x': -20, 'y':0, 'z':0}}, 
                        meta=dict())
test_fnc(lang_sequence)
test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))

## Remove Droplet method
xx = np.arange(7.5, 47.5, 5)
yy = np.arange(27.5, 37.5, 5)
x, y = np.meshgrid(xx, yy)
x = x.flatten()
y = y.flatten()
substrate = 0
test_fnc(dict(soe=['orchestrator/start'], params={'start':{'collectionkey' : 'substrate_{}'.format(substrate)}}, meta=dict()))
for i in range(len(x)):
    dx = x[i]
    dy = y[i]
    dz = config['lang']['safe_sample_pos'][2]
    sequence_run_1 = dict(soe=[f'lang/moveWaste_{2*i}', f'hamilton/pumpL_{5*i}', f'hamilton/pumpL_{5*i+1}',f'lang/RemoveDroplet_{i}', f'lang/moveSample_{i}', f'lang/moveDown_{i}', f'hamilton/pumpL_{5*i+2}'], 
                       params={f'moveWaste_{2*i}':{'x': -25, 'y':0, 'z':0},
                            f'pumpL_{5*i}': {'volume': 250, 'times': 1},
                            f'pumpL_{5*i+1}': {'volume': -250, 'times': 1},
                            f'RemoveDroplet_{i}': {'x':-25, 'y':0, 'z':0},
                            f'moveSample_{i}': {'x':dx, 'y':dy, 'z':dz}, 
                            f'moveDown_{i}': {'dz':0.049, 'steps':260, 'maxForce':2.5, 'threshold': 0.09},
                            f'pumpL_{5*i+2}': {'volume': 350, 'times': 1}}, 
                        meta=dict())
    sequence_run_2 = dict(soe=[f'hamilton/pumpL_{5*i+3}', f'lang/moveWaste_{2*i+1}', f'hamilton/pumpL_{5*i+4}'], 
                       params={f'pumpL_{5*i+3}': {'volume': -350, 'times': 1},
                            f'moveWaste_{2*i+1}':{'x': -25, 'y':0, 'z':0},
                            f'pumpL_{5*i+4}': {'volume': 350, 'times': 1}},
                        meta=dict())
    test_fnc(sequence_run_1)
    print(f'exp:{i}/{len(x)-1} is started, time: {str(datetime.datetime.now())}')
    time.sleep(180)
    test_fnc(sequence_run_2)
test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))

#x=-13.2, y=-4.8, z=8.4