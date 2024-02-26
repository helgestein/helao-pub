import requests
import json
import numpy as np
import pandas as pd
import random
import math
import sys
sys.path.append(r'../config')
sys.path.append('config')
from sdc_4 import config
import matplotlib.pyplot as plt
random.seed(0)

def test_fnc(sequence,thread=0):
    server = 'orchestrator'
    action = 'addExperiment'
    params = dict(experiment=json.dumps(sequence),thread=thread)
    print("requesting")
    requests.post("http://{}:{}/{}/{}".format(
        config['servers']['orchestrator']['host'], 13380, server, action), params=params).json()

def schwefel_function(x, y):
    comp = np.array([x, y])
    sch_comp = 20 * np.array(comp) - 500
    result = 0
    for index, element in enumerate(sch_comp):
        #print(f"index is {index} and element is {element}")
        result += - element * np.sin(np.sqrt(np.abs(element)))
    result = (-result) / 1000
    #const = 418.9829*2
    # const = (420.9687 + 500) / 20
    #result = result + const
    # result = (-1)*result
    return result

### schwefel
x_grid, y_grid = np.meshgrid([2.5 * i for i in range(21)], [2.5 * i for i in range(21)])
x, y = x_grid.flatten(), y_grid.flatten()
x_query = np.array([[i, j] for i, j in zip(x, y)])
first_arbitary_choice = random.choice(x_query)
dx0, dy0 = first_arbitary_choice[0], first_arbitary_choice[1]
y_query = [schwefel_function(x[0], x[1])for x in x_query]
z_con = np.array(y_query).reshape((len(x_grid), len(y_grid)))
query = json.dumps({'x_query': x_query.tolist(), 'y_query': y_query, 'z_con': z_con.tolist()})  
#dz = config['lang']['safe_sample_pos'][2]

def algebra(x, y):
    #result = 2*x*np.sin(y/2)+y*np.cos(x)-x*y/12-x*x/5-y**3/600
    a1, b1 = -15, 15
    a2, b2 = 5, -10
    a3, b3 = 22.5, 17.5
    sigma = 10
    return np.exp(-((x - a1)**2 + (y - b1)**2) / (2 * sigma**2)) + 5/4*np.exp(-((x - a2)**2 + (y - b2)**2) / (3 * sigma**2)) + 4/5*np.exp(-((x - a3)**2 + (y - b3)**2) / (4 * sigma**2))

def algebra_wafer(x, y):
    #result = 2*x*np.sin(y/2)+y*np.cos(x)-x*y/12-x*x/5-y**3/600
    a1, b1 = -7.5, 72.5
    a2, b2 = 22.5, 30
    a3, b3 = 42.5, 75
    sigma = 15
    return np.exp(-((x - a1)**2 + (y - b1)**2) / (2 * sigma**2)) + 5/4*np.exp(-((x - a2)**2 + (y - b2)**2) / (3 * sigma**2)) + 4/5*np.exp(-((x - a3)**2 + (y - b3)**2) / (4 * sigma**2))

### algebra
x_grid, y_grid = np.meshgrid(np.arange(-25, 27.5, 2.5),np.arange(-25, 27.5, 2.5))
x, y = x_grid.flatten(), y_grid.flatten()
x_query = np.array([[i, j] for i, j in zip(x, y)])
y_query = [algebra(x[0], x[1]) for x in x_query]
z_con = np.array(y_query).reshape((len(x_grid), len(y_grid)))
query = json.dumps({'x_query': x_query.tolist(), 'y_query': y_query, 'z_con': z_con.tolist()})  
first_arbitary_choice = random.choice(x_query)
dx0, dy0 = first_arbitary_choice[0], first_arbitary_choice[1]

### plot algebra
plt.figure(figsize=(10, 8))
sc = plt.scatter(X, Y, c=y_query, cmap=plt.cm.jet)
plt.colorbar(sc)  # Adding a color bar to represent the scale of z values
plt.title("2D Function Visualization")
plt.xlabel("X axis")
plt.ylabel("Y axis")
plt.grid(True)
plt.show()

### ALGEBRA

test_fnc(dict(soe=['orchestrator/start', 'lang/getPos_0', 'autolab/measure_0', 'measure/algebra_0', 'ml/sdc4_0'], 
            params={'start': {'collectionkey' : f'substrate_{substrate}'},
                    'getPos_0': {},
                    'autolab/measure_0': {'procedure': 'ocp_rs', 
                                            'setpointjson': json.dumps({'recordsignal': {'Duration': I0, 'Interval time in µs': 0.1}}),
                                            'plot': "tCV",
                                            'onoffafter': "off",
                                            'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                            'filename': 'substrate_{}_ocp_{}_{}.nox'.format(substrate, 0, 0),
                                            'parseinstructions':'recordsignal'},
                    'algebra_0': {'x': x0,'y': y0},
                    'sdc4_0': {'address':json.dumps([f'experiment_0:0/getPos_0/data/data/pos', f'experiment_0:0/schwefelFunction_0/data/key_y'])}},
            meta=dict()))

test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))

substrate = -999

### Real wafer coordinates
df = pd.read_csv(r'C:\Users\LaborRatte23-2\Documents\SDC functions\Python scripts\df_lim_109.csv').to_numpy()
random.seed(109)
XY, C, I, Q, m = df[:,0:2], df[:,2:5], df[:,-3], df[:,-2], df[:,-1] # correct currents when real test is used (CP)
X, Y = XY[:,0], XY[:,1]
x_query = np.array([[i, j] for i, j in zip(X, Y)])
query = json.dumps({'x_query': x_query.tolist(), 'c_query': C.tolist(), 'i_query': I.tolist(), 'q_query': Q.tolist(), 'm_query': m.tolist()})
id0 = random.randint(0, len(X))
x0, y0, I0 = X[id0], Y[id0], I[id0]

substrate = 109
z = 13.55

test_fnc(dict(soe=['orchestrator/start', f'lang/moveWaste_{0}', f'hamilton/pumpL_{0}', f'hamilton/pumpR_{0}', f'lang/moveWaste_{1}', 
                    f'lang/moveWaste_{2}', f'lang/moveWaste_{3}', f'lang/moveWaste_{4}', f'hamilton/pumpL_{1}', f'lang/moveSample_{0}',
                    f'lang/moveDown_{0}', f'lang/getPos_{0}', f'hamilton/pumpL_{2}', f'hamilton/pumpL_{3}', f'hamilton/pumpL_{4}', 
                    f'hamilton/pumpL_{5}', f'hamilton/pumpL_{6}', f'autolab/measure_{0}', f'autolab/measure_{1}', f'autolab/measure_{2}',
                    f'autolab/measure_{3}', f'autolab/measure_{4}', f'autolab/measure_{5}', f'autolab/measure_{6}', f'autolab/measure_{7}',
                    f'autolab/measure_{8}', f'autolab/measure_{9}', f'autolab/measure_{10}', f'autolab/measure_{11}', f'autolab/measure_{12}',
                    f'autolab/measure_{13}', f'hamilton/pumpL_{7}', f'lang/moveRel_{0}', f'hamilton/pumpL_{8}', f'lang/moveRel_{1}', 
                    f'hamilton/pumpL_{9}', f'lang/moveWaste_{5}', f'analysis/cp_{0}', f'analysis/ocp_{0}', f'analysis/eis0_{0}',
                    f'analysis/eis1_{0}', f'analysis/eis1_{1}', f'analysis/eis1_{2}', f'ml/activeLearningGaussian_{0}'], 
            params={'start': {'collectionkey' : f'substrate_{substrate}'},
                    f'moveWaste_{0}':{'x': 0, 'y':0, 'z': 0},
                    f'pumpL_{0}': {'volume': 125, 'times': 3},
                    f'pumpR_{0}': {'volume': 0, 'times': 1},
                    f'moveWaste_{1}':{'x': 25.3, 'y': -14.7, 'z': 9.2},
                    f'moveWaste_{2}':{'x': 25.3, 'y': -14.7, 'z': 0},
                    f'moveWaste_{3}':{'x': 25.3, 'y': -14.7, 'z': 9.2},
                    f'moveWaste_{4}':{'x': 25.3, 'y': -14.7, 'z': 0},
                    f'pumpL_{1}': {'volume': 0, 'times': 1},
                    f'moveSample_{0}': {'x': x0, 'y': y0, 'z': z}, 
                    f'moveDown_{0}': {'dz': 0.005, 'steps': 400, 'maxForce': 7900.0, 'threshold': 0.12},
                    f'getPos_{0}': {},
                    f'pumpL_{2}': {'volume': 10, 'times': 1},
                    f'pumpL_{3}': {'volume': -10, 'times': 1},
                    f'pumpL_{4}': {'volume': 10, 'times': 1},
                    f'pumpL_{5}': {'volume': -10, 'times': 1},
                    f'pumpL_{6}': {'volume': 30, 'times': 1},
                    f'measure_{0}':{'procedure': 'ocp_rs', 
                                    'setpointjson': json.dumps({'recordsignal': {'Duration': 90, 'Interval time in µs': 1}}),
                                    'plot': "tCV",
                                    'onoffafter': "off",
                                    'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                    'filename': 'substrate_{}_ocp_{}_{}.nox'.format(substrate, 0, 0),
                                    'parseinstructions':'recordsignal'},
                    f'measure_{1}':{'procedure': 'eis_fast',
                                    'setpointjson': json.dumps({'FHSetSetpointPotential': {'Setpoint value': None}}),
                                    'plot': 'impedance',
                                    'onoffafter': 'off',
                                    'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                    'filename': 'substrate_{}_eis_ocp_{:03d}_{}.nox'.format(substrate, 0, 0),
                                    'parseinstructions': ['FIAMeasPotentiostatic'],
                                    'substrate': substrate,
                                    'id': 0,
                                    'experiment': 0},
                    f'measure_{2}': {'procedure': 'charge',
                                    'setpointjson': json.dumps({'switchgalvanostatic': {'WE(1).Current range': round(math.log10(I0))},
                                                                'applycurrent': {'Setpoint value': -I0},
                                                                'recordsignal': {'Duration': 9000,
                                                                                 'Interval time in µs': 1}}),
                                    'plot': 'tCV',
                                    'onoffafter': 'off',
                                    'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                    'filename': 'substrate_{}_cp_charge_{:03d}_{}.nox'.format(substrate, 0, 1),
                                    'parseinstructions': 'recordsignal'},
                    f'measure_{3}': {'procedure': 'discharge',
                                    'setpointjson': json.dumps({'switchgalvanostatic': {'WE(1).Current range': round(math.log10(I0))},
                                                                'applycurrent': {'Setpoint value': I0},
                                                                'recordsignal': {'Duration': 9000,
                                                                                 'Interval time in µs': 1}}),
                                    'plot': 'tCV',
                                    'onoffafter': 'off',
                                    'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                    'filename': 'substrate_{}_cp_discharge_{:03d}_{}.nox'.format(substrate, 0, 1),
                                    'parseinstructions': 'recordsignal'},
                    f'measure_{4}':{'procedure': 'ocp_rs', 
                                    'setpointjson': json.dumps({'recordsignal': {'Duration': 300, 'Interval time in µs': 1}}),
                                    'plot': "tCV",
                                    'onoffafter': "off",
                                    'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                    'filename': 'substrate_{}_ocp_{}_{}.nox'.format(substrate, 0, 1),
                                    'parseinstructions':'recordsignal'},
                    f'measure_{5}':{'procedure': 'eis',
                                    'setpointjson': json.dumps({'FHSetSetpointPotential': {'Setpoint value': None}}),
                                    'plot': 'impedance',
                                    'onoffafter': 'off',
                                    'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                    'filename': 'substrate_{}_eis_ocp_{:03d}_{}.nox'.format(substrate, 0, 1),
                                    'parseinstructions': ['FIAMeasPotentiostatic'],
                                    'substrate': substrate,
                                    'id': 0,
                                    'experiment': 1},
                    f'measure_{6}': {'procedure': 'charge',
                                    'setpointjson': json.dumps({'switchgalvanostatic': {'WE(1).Current range': round(math.log10(I0))},
                                                                'applycurrent': {'Setpoint value': -I0},
                                                                'recordsignal': {'Duration': 9000,
                                                                                 'Interval time in µs': 1}}),
                                    'plot': 'tCV',
                                    'onoffafter': 'off',
                                    'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                    'filename': 'substrate_{}_cp_charge_{:03d}_{}.nox'.format(substrate, 0, 2),
                                    'parseinstructions': 'recordsignal'},
                    f'measure_{7}': {'procedure': 'discharge',
                                    'setpointjson': json.dumps({'switchgalvanostatic': {'WE(1).Current range': round(math.log10(I0))},
                                                                'applycurrent': {'Setpoint value': I0},
                                                                'recordsignal': {'Duration': 9000,
                                                                                 'Interval time in µs': 1}}),
                                    'plot': 'tCV',
                                    'onoffafter': 'off',
                                    'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                    'filename': 'substrate_{}_cp_discharge_{:03d}_{}.nox'.format(substrate, 0, 2),
                                    'parseinstructions': 'recordsignal'},
                    f'measure_{8}':{'procedure': 'ocp_rs', 
                                    'setpointjson': json.dumps({'recordsignal': {'Duration': 300, 'Interval time in µs': 1}}),
                                    'plot': "tCV",
                                    'onoffafter': "off",
                                    'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                    'filename': 'substrate_{}_ocp_{}_{}.nox'.format(substrate, 0, 2),
                                    'parseinstructions':'recordsignal'},
                    f'measure_{9}':{'procedure': 'eis',
                                    'setpointjson': json.dumps({'FHSetSetpointPotential': {'Setpoint value': None}}),
                                    'plot': 'impedance',
                                    'onoffafter': 'off',
                                    'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                    'filename': 'substrate_{}_eis_ocp_{:03d}_{}.nox'.format(substrate, 0, 2),
                                    'parseinstructions': ['FIAMeasPotentiostatic'],
                                    'substrate': substrate,
                                    'id': 0,
                                    'experiment': 2},
                    f'measure_{10}': {'procedure': 'charge',
                                    'setpointjson': json.dumps({'switchgalvanostatic': {'WE(1).Current range': round(math.log10(I0))},
                                                                'applycurrent': {'Setpoint value': -I0},
                                                                'recordsignal': {'Duration': 9000,
                                                                                 'Interval time in µs': 1}}),
                                    'plot': 'tCV',
                                    'onoffafter': 'off',
                                    'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                    'filename': 'substrate_{}_cp_charge_{:03d}_{}.nox'.format(substrate, 0, 3),
                                    'parseinstructions': 'recordsignal'},
                    f'measure_{11}': {'procedure': 'discharge',
                                    'setpointjson': json.dumps({'switchgalvanostatic': {'WE(1).Current range': round(math.log10(I0))},
                                                                'applycurrent': {'Setpoint value': I0},
                                                                'recordsignal': {'Duration': 9000,
                                                                                 'Interval time in µs': 1}}),
                                    'plot': 'tCV',
                                    'onoffafter': 'off',
                                    'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                    'filename': 'substrate_{}_cp_discharge_{:03d}_{}.nox'.format(substrate, 0, 3),
                                    'parseinstructions': 'recordsignal'},
                    f'measure_{12}':{'procedure': 'ocp_rs', 
                                    'setpointjson': json.dumps({'recordsignal': {'Duration': 300, 'Interval time in µs': 1}}),
                                    'plot': "tCV",
                                    'onoffafter': "off",
                                    'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                    'filename': 'substrate_{}_ocp_{}_{}.nox'.format(substrate, 0, 3),
                                    'parseinstructions':'recordsignal'},
                    f'measure_{13}':{'procedure': 'eis',
                                    'setpointjson': json.dumps({'FHSetSetpointPotential': {'Setpoint value': None}}),
                                    'plot': 'impedance',
                                    'onoffafter': 'off',
                                    'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                    'filename': 'substrate_{}_eis_ocp_{:03d}_{}.nox'.format(substrate, 0, 3),
                                    'parseinstructions': ['FIAMeasPotentiostatic'],
                                    'substrate': substrate,
                                    'id': 0,
                                    'experiment': 3},
                    f'pumpL_{7}': {'volume': -75, 'times': 1},
                    f'moveRel_{0}':{'dx': 0, 'dy':0, 'dz':-0.5},
                    f'pumpL_{8}': {'volume': -50, 'times': 1},
                    f'moveRel_{1}':{'dx': 0, 'dy':0, 'dz':-0.5},
                    f'pumpL_{9}': {'volume': -50, 'times': 1},
                    f'moveWaste_{5}':{'x': 0, 'y':0, 'z': 0},
                    f'cp_{0}': {'query': query, 'address':json.dumps([f'experiment_0:0/moveSample_{0}/parameters/x',
                                                                           f'experiment_0:0/moveSample_{0}/parameters/y',
                                                                           f'experiment_0:0/measure_{2}/data/data/recordsignal/Corrected time',
                                                                           f'experiment_0:0/measure_{2}/data/data/recordsignal/WE(1).Current',
                                                                           f'experiment_0:0/measure_{2}/data/data/recordsignal/WE(1).Potential',
                                                                           f'experiment_0:0/measure_{3}/data/data/recordsignal/Corrected time',
                                                                           f'experiment_0:0/measure_{3}/data/data/recordsignal/WE(1).Current',
                                                                           f'experiment_0:0/measure_{3}/data/data/recordsignal/WE(1).Potential',
                                                                           f'experiment_0:0/measure_{6}/data/data/recordsignal/Corrected time',
                                                                           f'experiment_0:0/measure_{6}/data/data/recordsignal/WE(1).Current',
                                                                           f'experiment_0:0/measure_{6}/data/data/recordsignal/WE(1).Potential',
                                                                           f'experiment_0:0/measure_{7}/data/data/recordsignal/Corrected time',
                                                                           f'experiment_0:0/measure_{7}/data/data/recordsignal/WE(1).Current',
                                                                           f'experiment_0:0/measure_{7}/data/data/recordsignal/WE(1).Potential',
                                                                           f'experiment_0:0/measure_{10}/data/data/recordsignal/Corrected time',
                                                                           f'experiment_0:0/measure_{10}/data/data/recordsignal/WE(1).Current',
                                                                           f'experiment_0:0/measure_{10}/data/data/recordsignal/WE(1).Potential',
                                                                           f'experiment_0:0/measure_{11}/data/data/recordsignal/Corrected time',
                                                                           f'experiment_0:0/measure_{11}/data/data/recordsignal/WE(1).Current',
                                                                           f'experiment_0:0/measure_{11}/data/data/recordsignal/WE(1).Potential'])},
                    f'ocp_{0}': {'address':json.dumps([f'experiment_{0}:0/measure_{14*(0)}/data/data/recordsignal/WE(1).Potential',
                                                        f'experiment_{0}:0/measure_{14*(0)+4}/data/data/recordsignal/WE(1).Potential',
                                                        f'experiment_{0}:0/measure_{14*(0)+8}/data/data/recordsignal/WE(1).Potential',
                                                        f'experiment_{0}:0/measure_{14*(0)+12}/data/data/recordsignal/WE(1).Potential'])},
                    f'eis0_{0}': {'run': 0, 'address':json.dumps([f"experiment_{0}:0/measure_{1}/data/data/FIAMeasPotentiostatic/Z'",
                                                                f"experiment_{0}:0/measure_{1}/data/data/FIAMeasPotentiostatic/-Z''",
                                                                f"experiment_{0}:0/measure_{1}/data/data/FIAMeasPotentiostatic/Frequency"])},  
                    f'eis1_{0}': {'run': 1, 'address':json.dumps([f"experiment_{0}:0/measure_{5}/data/data/FIAMeasPotentiostatic/Z'",
                                                                f"experiment_{0}:0/measure_{5}/data/data/FIAMeasPotentiostatic/-Z''",
                                                                f"experiment_{0}:0/measure_{5}/data/data/FIAMeasPotentiostatic/Frequency"])},
                    f'eis1_{1}': {'run': 2, 'address':json.dumps([f"experiment_{0}:0/measure_{9}/data/data/FIAMeasPotentiostatic/Z'",
                                                                f"experiment_{0}:0/measure_{9}/data/data/FIAMeasPotentiostatic/-Z''",
                                                                f"experiment_{0}:0/measure_{9}/data/data/FIAMeasPotentiostatic/Frequency"])},
                    f'eis1_{2}': {'run': 3, 'address':json.dumps([f"experiment_{0}:0/measure_{13}/data/data/FIAMeasPotentiostatic/Z'",
                                                                f"experiment_{0}:0/measure_{13}/data/data/FIAMeasPotentiostatic/-Z''",
                                                                f"experiment_{0}:0/measure_{13}/data/data/FIAMeasPotentiostatic/Frequency"])},
                    f'activeLearningGaussian_{0}': {'name': 'sdc_4', 'num': int(0), 'query': query, 'address':f'experiment_0:0/cp_0/data'}},
            meta=dict()))

for i in range(28, 29):
    test_fnc(dict(soe=[f'orchestrator/modify_{i}', f'lang/moveWaste_{6*(i+1)}', f'hamilton/pumpL_{10*(i+1)}', f'hamilton/pumpR_{i+1}', f'lang/moveWaste_{6*(i+1)+1}', 
                    f'lang/moveWaste_{6*(i+1)+2}', f'lang/moveWaste_{6*(i+1)+3}', f'lang/moveWaste_{6*(i+1)+4}', f'hamilton/pumpL_{10*(i+1)+1}', f'lang/moveSample_{i+1}',
                    f'lang/moveDown_{i+1}', f'lang/getPos_{i+1}', f'hamilton/pumpL_{10*(i+1)+2}', f'hamilton/pumpL_{10*(i+1)+3}', f'hamilton/pumpL_{10*(i+1)+4}', 
                    f'hamilton/pumpL_{10*(i+1)+5}', f'hamilton/pumpL_{10*(i+1)+6}', f'autolab/measure_{14*(i+1)}', f'autolab/measure_{14*(i+1)+1}', f'autolab/measure_{14*(i+1)+2}',
                    f'autolab/measure_{14*(i+1)+3}', f'autolab/measure_{14*(i+1)+4}', f'autolab/measure_{14*(i+1)+5}', f'autolab/measure_{14*(i+1)+6}', f'autolab/measure_{14*(i+1)+7}',
                    f'autolab/measure_{14*(i+1)+8}', f'autolab/measure_{14*(i+1)+9}', f'autolab/measure_{14*(i+1)+10}', f'autolab/measure_{14*(i+1)+11}', f'autolab/measure_{14*(i+1)+12}',
                    f'autolab/measure_{14*(i+1)+13}', f'hamilton/pumpL_{10*(i+1)+7}', f'lang/moveRel_{2*(i+1)}', f'hamilton/pumpL_{10*(i+1)+8}', f'lang/moveRel_{2*(i+1)+1}',
                    f'hamilton/pumpL_{10*(i+1)+9}', f'lang/moveWaste_{6*(i+1)+5}', f'analysis/cp_{i+1}', f'analysis/ocp_{i+1}', f'analysis/eis0_{(i+1)}',
                    f'analysis/eis1_{3*(i+1)}', f'analysis/eis1_{3*(i+1)+1}', f'analysis/eis1_{3*(i+1)+2}', f'ml/activeLearningGaussian_{i+1}'],
            params={f'modify_{i}': {'addresses':[f'experiment_{i}:0/activeLearningGaussian_{i}/data/next_x',
                                                 f'experiment_{i}:0/activeLearningGaussian_{i}/data/next_y',
                                                 f'experiment_{i}:0/activeLearningGaussian_{i}/data/next_ci',
                                                 f'experiment_{i}:0/activeLearningGaussian_{i}/data/next_di',
                                                 f'experiment_{i}:0/activeLearningGaussian_{i}/data/next_ci',
                                                 f'experiment_{i}:0/activeLearningGaussian_{i}/data/next_di',
                                                 f'experiment_{i}:0/activeLearningGaussian_{i}/data/next_ci',
                                                 f'experiment_{i}:0/activeLearningGaussian_{i}/data/next_di'],
                                    'pointers':[f'moveSample_{i+1}/x', f'moveSample_{i+1}/y', f'measure_{14*(i+1)+2}/setpointjson', f'measure_{14*(i+1)+3}/setpointjson',
                                                f'measure_{14*(i+1)+6}/setpointjson', f'measure_{14*(i+1)+7}/setpointjson', f'measure_{14*(i+1)+10}/setpointjson', f'measure_{14*(i+1)+11}/setpointjson']}, # correct ml_action for measure_cp
                    f'moveWaste_{6*(i+1)}':{'x': 0, 'y':0, 'z': 0},
                    f'pumpL_{10*(i+1)}': {'volume': 125, 'times': 3},
                    f'pumpR_{(i+1)}': {'volume': 0, 'times': 1},
                    f'moveWaste_{6*(i+1)+1}':{'x': 25.3, 'y': -14.7, 'z': 9.2},
                    f'moveWaste_{6*(i+1)+2}':{'x': 25.3, 'y': -14.7, 'z': 0},
                    f'moveWaste_{6*(i+1)+3}':{'x': 25.3, 'y': -14.7, 'z': 9.2},
                    f'moveWaste_{6*(i+1)+4}':{'x': 25.3, 'y': -14.7, 'z': 0},
                    f'pumpL_{10*(i+1)+1}': {'volume': 0, 'times': 1},
                    f'moveSample_{i+1}': {'x': '?', 'y': '?', 'z': z}, 
                    f'moveDown_{i+1}': {'dz': 0.005, 'steps': 400, 'maxForce': 7900.0, 'threshold': 0.12},
                    f'getPos_{i+1}': {},
                    f'pumpL_{10*(i+1)+2}': {'volume': 10, 'times': 1},
                    f'pumpL_{10*(i+1)+3}': {'volume': -10, 'times': 1},
                    f'pumpL_{10*(i+1)+4}': {'volume': 10, 'times': 1},
                    f'pumpL_{10*(i+1)+5}': {'volume': -10, 'times': 1},
                    f'pumpL_{10*(i+1)+6}': {'volume': 30, 'times': 1},
                    f'measure_{14*(i+1)}': {'procedure': 'ocp_rs', 
                                        'setpointjson': json.dumps({'recordsignal': {'Duration': 90, 'Interval time in µs': 1}}),
                                        'plot': "tCV",
                                        'onoffafter': "off",
                                        'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                        'filename': 'substrate_{}_ocp_{}_{}.nox'.format(substrate, int(i+1), 0),
                                        'parseinstructions':'recordsignal'},
                    f'measure_{14*(i+1)+1}': {'procedure': 'eis_fast',
                                        'setpointjson': json.dumps({'FHSetSetpointPotential': {'Setpoint value': None}}),
                                        'plot': 'impedance',
                                        'onoffafter': 'off',
                                        'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                        'filename': 'substrate_{}_eis_ocp_{:03d}_{}.nox'.format(substrate, int(i+1), 0),
                                        'parseinstructions': ['FIAMeasPotentiostatic'],
                                        'substrate': substrate,
                                        'id': int(i+1),
                                        'experiment': 0},
                    f'measure_{14*(i+1)+2}': {'procedure': 'charge',
                                           'setpointjson': '?',
                                           'plot': 'tCV',
                                           'onoffafter': 'off',
                                           'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                           'filename': 'substrate_{}_cp_charge_{:03d}_{}.nox'.format(substrate, int(i+1), 1),
                                           'parseinstructions': 'recordsignal'},
                    f'measure_{14*(i+1)+3}': {'procedure': 'discharge',
                                            'setpointjson': '?',
                                            'plot': 'tCV',
                                            'onoffafter': 'off',
                                            'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                            'filename': 'substrate_{}_cp_discharge_{:03d}_{}.nox'.format(substrate, int(i+1), 1),
                                            'parseinstructions': 'recordsignal'},
                    f'measure_{14*(i+1)+4}': {'procedure': 'ocp_rs', 
                                            'setpointjson': json.dumps({'recordsignal': {'Duration': 300, 'Interval time in µs': 1}}),
                                            'plot': "tCV",
                                            'onoffafter': "off",
                                            'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                            'filename': 'substrate_{}_ocp_{}_{}.nox'.format(substrate, int(i+1), 1),
                                            'parseinstructions':'recordsignal'},
                    f'measure_{14*(i+1)+5}': {'procedure': 'eis',
                                            'setpointjson': json.dumps({'FHSetSetpointPotential': {'Setpoint value': None}}),
                                            'plot': 'impedance',
                                            'onoffafter': 'off',
                                            'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                            'filename': 'substrate_{}_eis_ocp_{:03d}_{}.nox'.format(substrate, int(i+1), 1),
                                            'parseinstructions': ['FIAMeasPotentiostatic'],
                                            'substrate': substrate,
                                            'id': int(i+1),
                                            'experiment': 1},
                    f'measure_{14*(i+1)+6}': {'procedure': 'charge',
                                           'setpointjson': '?',
                                           'plot': 'tCV',
                                           'onoffafter': 'off',
                                           'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                           'filename': 'substrate_{}_cp_charge_{:03d}_{}.nox'.format(substrate, int(i+1), 2),
                                           'parseinstructions': 'recordsignal'},
                    f'measure_{14*(i+1)+7}': {'procedure': 'discharge',
                                            'setpointjson': '?',
                                            'plot': 'tCV',
                                            'onoffafter': 'off',
                                            'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                            'filename': 'substrate_{}_cp_discharge_{:03d}_{}.nox'.format(substrate, int(i+1), 2),
                                            'parseinstructions': 'recordsignal'},
                    f'measure_{14*(i+1)+8}': {'procedure': 'ocp_rs', 
                                            'setpointjson': json.dumps({'recordsignal': {'Duration': 300, 'Interval time in µs': 1}}),
                                            'plot': "tCV",
                                            'onoffafter': "off",
                                            'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                            'filename': 'substrate_{}_ocp_{}_{}.nox'.format(substrate, int(i+1), 2),
                                            'parseinstructions':'recordsignal'},
                    f'measure_{14*(i+1)+9}': {'procedure': 'eis',
                                            'setpointjson': json.dumps({'FHSetSetpointPotential': {'Setpoint value': None}}),
                                            'plot': 'impedance',
                                            'onoffafter': 'off',
                                            'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                            'filename': 'substrate_{}_eis_ocp_{:03d}_{}.nox'.format(substrate, int(i+1), 2),
                                            'parseinstructions': ['FIAMeasPotentiostatic'],
                                            'substrate': substrate,
                                            'id': int(i+1),
                                            'experiment': 2},
                    f'measure_{14*(i+1)+10}': {'procedure': 'charge',
                                           'setpointjson': '?',
                                           'plot': 'tCV',
                                           'onoffafter': 'off',
                                           'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                           'filename': 'substrate_{}_cp_charge_{:03d}_{}.nox'.format(substrate, int(i+1), 3),
                                           'parseinstructions': 'recordsignal'},
                    f'measure_{14*(i+1)+11}': {'procedure': 'discharge',
                                            'setpointjson': '?',
                                            'plot': 'tCV',
                                            'onoffafter': 'off',
                                            'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                            'filename': 'substrate_{}_cp_discharge_{:03d}_{}.nox'.format(substrate, int(i+1), 3),
                                            'parseinstructions': 'recordsignal'},
                    f'measure_{14*(i+1)+12}': {'procedure': 'ocp_rs', 
                                            'setpointjson': json.dumps({'recordsignal': {'Duration': 300, 'Interval time in µs': 1}}),
                                            'plot': "tCV",
                                            'onoffafter': "off",
                                            'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                            'filename': 'substrate_{}_ocp_{}_{}.nox'.format(substrate, int(i+1), 3),
                                            'parseinstructions':'recordsignal'},
                    f'measure_{14*(i+1)+13}': {'procedure': 'eis',
                                            'setpointjson': json.dumps({'FHSetSetpointPotential': {'Setpoint value': None}}),
                                            'plot': 'impedance',
                                            'onoffafter': 'off',
                                            'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                            'filename': 'substrate_{}_eis_ocp_{:03d}_{}.nox'.format(substrate, int(i+1), 3),
                                            'parseinstructions': ['FIAMeasPotentiostatic'],
                                            'substrate': substrate,
                                            'id': int(i+1),
                                            'experiment': 3},
                    f'pumpL_{10*(i+1)+7}': {'volume': -75, 'times': 1},
                    f'moveRel_{2*(i+1)}':{'dx': 0, 'dy':0, 'dz':-0.5},
                    f'pumpL_{10*(i+1)+8}': {'volume': -50, 'times': 1},
                    f'moveRel_{2*(i+1)+1}':{'dx': 0, 'dy':0, 'dz':-0.5},
                    f'pumpL_{10*(i+1)+9}': {'volume': -50, 'times': 1},
                    f'moveWaste_{6*(i+1)+5}':{'x': 0, 'y':0, 'z': 0},
                    f'cp_{i+1}':{'query': query, 'address':json.dumps([f'experiment_{i+1}:0/moveSample_{i+1}/parameters/x',
                                                                            f'experiment_{i+1}:0/moveSample_{i+1}/parameters/y',
                                                                            f'experiment_{i+1}:0/measure_{14*(i+1)+2}/data/data/recordsignal/Corrected time',
                                                                            f'experiment_{i+1}:0/measure_{14*(i+1)+2}/data/data/recordsignal/WE(1).Current',
                                                                            f'experiment_{i+1}:0/measure_{14*(i+1)+2}/data/data/recordsignal/WE(1).Potential',
                                                                            f'experiment_{i+1}:0/measure_{14*(i+1)+3}/data/data/recordsignal/Corrected time',
                                                                            f'experiment_{i+1}:0/measure_{14*(i+1)+3}/data/data/recordsignal/WE(1).Current',
                                                                            f'experiment_{i+1}:0/measure_{14*(i+1)+3}/data/data/recordsignal/WE(1).Potential',
                                                                            f'experiment_{i+1}:0/measure_{14*(i+1)+6}/data/data/recordsignal/Corrected time',
                                                                            f'experiment_{i+1}:0/measure_{14*(i+1)+6}/data/data/recordsignal/WE(1).Current',
                                                                            f'experiment_{i+1}:0/measure_{14*(i+1)+6}/data/data/recordsignal/WE(1).Potential',
                                                                            f'experiment_{i+1}:0/measure_{14*(i+1)+7}/data/data/recordsignal/Corrected time',
                                                                            f'experiment_{i+1}:0/measure_{14*(i+1)+7}/data/data/recordsignal/WE(1).Current',
                                                                            f'experiment_{i+1}:0/measure_{14*(i+1)+7}/data/data/recordsignal/WE(1).Potential',
                                                                            f'experiment_{i+1}:0/measure_{14*(i+1)+10}/data/data/recordsignal/Corrected time',
                                                                            f'experiment_{i+1}:0/measure_{14*(i+1)+10}/data/data/recordsignal/WE(1).Current',
                                                                            f'experiment_{i+1}:0/measure_{14*(i+1)+10}/data/data/recordsignal/WE(1).Potential',
                                                                            f'experiment_{i+1}:0/measure_{14*(i+1)+11}/data/data/recordsignal/Corrected time',
                                                                            f'experiment_{i+1}:0/measure_{14*(i+1)+11}/data/data/recordsignal/WE(1).Current',
                                                                            f'experiment_{i+1}:0/measure_{14*(i+1)+11}/data/data/recordsignal/WE(1).Potential'])},
                    f'ocp_{i+1}': {'address':json.dumps([f'experiment_{i+1}:0/measure_{14*(i+1)}/data/data/recordsignal/WE(1).Potential',
                                                        f'experiment_{i+1}:0/measure_{14*(i+1)+4}/data/data/recordsignal/WE(1).Potential',
                                                        f'experiment_{i+1}:0/measure_{14*(i+1)+8}/data/data/recordsignal/WE(1).Potential',
                                                        f'experiment_{i+1}:0/measure_{14*(i+1)+12}/data/data/recordsignal/WE(1).Potential'])},
                    f'eis0_{(i+1)}': {'run': int(4*(i+1)), 'address':json.dumps([f"experiment_{i+1}:0/measure_{14*(i+1)+1}/data/data/FIAMeasPotentiostatic/Z'",
                                                                                f"experiment_{i+1}:0/measure_{14*(i+1)+1}/data/data/FIAMeasPotentiostatic/-Z''",
                                                                                f"experiment_{i+1}:0/measure_{14*(i+1)+1}/data/data/FIAMeasPotentiostatic/Frequency"])},  
                    f'eis1_{3*(i+1)}': {'run': int(4*(i+1)+1), 'address':json.dumps([f"experiment_{i+1}:0/measure_{14*(i+1)+5}/data/data/FIAMeasPotentiostatic/Z'",
                                                                                f"experiment_{i+1}:0/measure_{14*(i+1)+5}/data/data/FIAMeasPotentiostatic/-Z''",
                                                                                f"experiment_{i+1}:0/measure_{14*(i+1)+5}/data/data/FIAMeasPotentiostatic/Frequency"])},
                    f'eis1_{3*(i+1)+1}': {'run': int(4*(i+1)+2), 'address':json.dumps([f"experiment_{i+1}:0/measure_{14*(i+1)+9}/data/data/FIAMeasPotentiostatic/Z'",
                                                                                f"experiment_{i+1}:0/measure_{14*(i+1)+9}/data/data/FIAMeasPotentiostatic/-Z''",
                                                                                f"experiment_{i+1}:0/measure_{14*(i+1)+9}/data/data/FIAMeasPotentiostatic/Frequency"])},
                    f'eis1_{3*(i+1)+2}': {'run': int(4*(i+1)+3), 'address':json.dumps([f"experiment_{i+1}:0/measure_{14*(i+1)+13}/data/data/FIAMeasPotentiostatic/Z'",
                                                                                f"experiment_{i+1}:0/measure_{14*(i+1)+13}/data/data/FIAMeasPotentiostatic/-Z''",
                                                                                f"experiment_{i+1}:0/measure_{14*(i+1)+13}/data/data/FIAMeasPotentiostatic/Frequency"])},
                    f'activeLearningGaussian_{i+1}': {'name': 'sdc_4', 'num': int(i+1), 'query': query, 'address':f'experiment_{i+1}:0/cp_{i+1}/data'}}, 
                  meta=dict()))









###
test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))



























### SCHWEFEL

test_fnc(dict(soe=['orchestrator/start', 'lang/getPos_0', 'measure/schwefelFunction_0', 'ml/sdc4_0'], 
            params={'start': {'collectionkey' : f'substrate_{substrate}'},
                    'getPos_0': {},
                    'schwefelFunction_0': {'x':dx0,'y':dy0},
                    'sdc4_0': {'address':json.dumps([f'experiment_0:0/getPos_0/data/data/pos', f'experiment_0:0/schwefelFunction_0/data/key_y'])}},
            meta=dict()))

test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))

substrate = -999
n = 50

test_fnc(dict(soe=['orchestrator/start', 'lang/getPos_0', 'measure/schwefelFunction_0', 'analysis/dummy_0', 'ml/activeLearningGaussian_0'], 
            params={'start': {'collectionkey' : f'substrate_{substrate}'},
                    'getPos_0': {},
                    'schwefelFunction_0': {'x':dx0,'y':dy0},
                    'dummy_0': {'address':json.dumps([f'experiment_0:0/schwefelFunction_0/parameters/x',
                                                      f'experiment_0:0/schwefelFunction_0/parameters/y',
                                                      f'experiment_0:0/schwefelFunction_0/data/key_y'])},
                    'activeLearningGaussian_0': {'name': 'sdc_4', 'num': int(1), 'query': query, 'address':f'experiment_0:0/dummy_0/data'}},
            meta=dict()))

for i in range(n):
    test_fnc(dict(soe=[f'orchestrator/modify_{i}',f'lang/getPos_{i+1}', f'measure/schwefelFunction_{i+1}', f'analysis/dummy_{i+1}', f'ml/activeLearningGaussian_{i+1}'],
                  params={f'modify_{i}': {'addresses':[f'experiment_{i}:0/activeLearningGaussian_{i}/data/next_x',
                                                       f'experiment_{i}:0/activeLearningGaussian_{i}/data/next_y'],
                                            'pointers':[f'schwefelFunction_{i+1}/x',f'schwefelFunction_{i+1}/y']},
                            f'getPos_{i+1}': {},
                            f'schwefelFunction_{i+1}':{'x':'?','y':'?'},
                            f'dummy_{i+1}':{'address':json.dumps([f'experiment_{i+1}:0/schwefelFunction_{i+1}/parameters/x',
                                                                  f'experiment_{i+1}:0/schwefelFunction_{i+1}/parameters/y',
                                                                  f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/key_y'])},
                            f'activeLearningGaussian_{i+1}': {'name': 'sdc_4', 'num': int(i+1), 'query': query, 'address':f'experiment_{i+1}:0/dummy_{i+1}/data'}}, 
                  meta=dict()))

test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))










test_fnc(dict(soe=['orchestrator/start','lang:2/moveWaste_0', 'lang:2/RemoveDroplet_0',
                   'lang:2/moveSample_0','lang:2/moveAbs_0','lang:2/moveDown_0','measure:2/schwefelFunction_0','analysis/dummy_0'], 
            params={'start': {'collectionkey' : 'al_sequential'},
                    'moveWaste_0':{'x': 0, 'y':0, 'z':0},
                    'RemoveDroplet_0': {'x':0, 'y':0, 'z':0},
                    'moveSample_0': {'x':0, 'y':0, 'z':0},
                    'moveAbs_0': {'dx':dx0, 'dy':dy0, 'dz':dz}, 
                    'moveDown_0': {'dz':0.12, 'steps':4, 'maxForce':1.4, 'threshold': 0.13},
                    'schwefelFunction_0':{'x':dx0,'y':dy0},
                    'dummy_0':{'x_address':'experiment_0:0/schwefelFunction_0/data/parameters/x',
                                'y_address':'experiment_0:0/schwefelFunction_0/data/parameters/y',
                                'schwefel_address':'experiment_0:0/schwefelFunction_0/data/data/key_y'}}, 
            meta=dict()))

for i in range(n):
    test_fnc(dict(soe=[f'ml/activeLearningGaussianParallel_{i}',f'orchestrator/modify_{i}',f'lang:2/moveWaste_{i+1}', f'lang:2/RemoveDroplet_{i+1}',
                       f'lang:2/moveSample_{i+1}',f'lang:2/moveAbs_{i+1}',f'lang:2/moveDown_{i+1}',
                       f'measure:2/schwefelFunction_{i+1}',f'analysis/dummy_{i+1}'], 
                  params={f'activeLearningGaussianParallel_{i}':{'name': 'sdc_2', 'num': int(i+1), 'query': query, 'address':f'experiment_{i}:0/dummy_{i}/data/data'},
                            f'modify_{i}': {'addresses':[f'experiment_{i+1}:0/activeLearningGaussianParallel_{i}/data/data/next_x',
                                                         f'experiment_{i+1}:0/activeLearningGaussianParallel_{i}/data/data/next_y',
                                                         f'experiment_{i+1}:0/activeLearningGaussianParallel_{i}/data/data/next_x',
                                                         f'experiment_{i+1}:0/activeLearningGaussianParallel_{i}/data/data/next_y'],
                                            'pointers':[f'schwefelFunction_{i+1}/x',f'schwefelFunction_{i+1}/y',
                                                        f'moveAbs_{i+1}/dx', f'moveAbs_{i+1}/dy']},
                            f'moveWaste_{i+1}':{'x': 0, 'y':0, 'z':0},
                            f'RemoveDroplet_{i+1}': {'x':0, 'y':0, 'z':0},
                            f'moveSample_{i+1}': {'x':0, 'y':0, 'z':0},
                            f'moveAbs_{i+1}': {'dx':'?', 'dy':'?', 'dz':dz}, 
                            f'moveDown_{i+1}': {'dz':0.12, 'steps':4, 'maxForce':1.4, 'threshold': 0.13},
                            f'schwefelFunction_{i+1}':{'x':'?','y':'?'},
                            f'dummy_{i+1}':{'x_address':f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/parameters/x',
                                            'y_address':f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/parameters/y',
                                            'schwefel_address':f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/data/key_y'}}, 
                  meta=dict()))

test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))