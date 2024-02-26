import requests
import json
import numpy as np
import pandas as pd
import random
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

### Real wafer coordinates
df = pd.read_csv(r'C:\Users\LaborRatte23-2\Documents\SDC functions\Python scripts\df_lim.csv').to_numpy()
XY, C, I, Q = df[:,0:2], df[:,2:5], df[:,-2], df[:,-1]
X = -XY[:,0]
Y = XY[:,1]
x_query = np.array([[i, j] for i, j in zip(X, Y)])
#y_query = Q
y_query = [algebra_wafer(x[0], x[1]) for x in x_query]
query = json.dumps({'x_query': x_query.tolist(), 'y_query': y_query})
first_arbitary_choice = random.choice(x_query)
dx0, dy0 = first_arbitary_choice[0], first_arbitary_choice[1]

substrate = -999

### ALGEBRA

test_fnc(dict(soe=['orchestrator/start', 'lang/getPos_0', 'measure/algebra_0', 'ml/sdc4_0'], 
            params={'start': {'collectionkey' : f'substrate_{substrate}'},
                    'getPos_0': {},
                    'algebra_0': {'x':dx0,'y':dy0},
                    'sdc4_0': {'address':json.dumps([f'experiment_0:0/getPos_0/data/data/pos', f'experiment_0:0/schwefelFunction_0/data/key_y'])}},
            meta=dict()))

test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))

substrate = -999

n = 30

test_fnc(dict(soe=['orchestrator/start', 'lang/getPos_0', 'measure/algebra_0', 'analysis/dummy_0', 'ml/activeLearningGaussian_0'], 
            params={'start': {'collectionkey' : f'substrate_{substrate}'},
                    'getPos_0': {},
                    'algebra_0': {'x':dx0,'y':dy0},
                    'dummy_0': {'address':json.dumps([f'experiment_0:0/algebra_0/parameters/x',
                                                      f'experiment_0:0/algebra_0/parameters/y',
                                                      f'experiment_0:0/algebra_0/data/key_y'])},
                    'activeLearningGaussian_0': {'name': 'sdc_4', 'num': int(0), 'query': query, 'address':f'experiment_0:0/dummy_0/data'}},
            meta=dict()))

for i in range(n):
    test_fnc(dict(soe=[f'orchestrator/modify_{i}',f'lang/getPos_{i+1}', f'measure/algebra_{i+1}', f'analysis/dummy_{i+1}', f'ml/activeLearningGaussian_{i+1}'],
                  params={f'modify_{i}': {'addresses':[f'experiment_{i}:0/activeLearningGaussian_{i}/data/next_x',
                                                       f'experiment_{i}:0/activeLearningGaussian_{i}/data/next_y'],
                                            'pointers':[f'algebra_{i+1}/x',f'algebra_{i+1}/y']},
                            f'getPos_{i+1}': {},
                            f'algebra_{i+1}':{'x':'?','y':'?'},
                            f'dummy_{i+1}':{'address':json.dumps([f'experiment_{i+1}:0/algebra_{i+1}/parameters/x',
                                                                  f'experiment_{i+1}:0/algebra_{i+1}/parameters/y',
                                                                  f'experiment_{i+1}:0/algebra_{i+1}/data/key_y'])},
                            f'activeLearningGaussian_{i+1}': {'name': 'sdc_4', 'num': int(i+1), 'query': query, 'address':f'experiment_{i+1}:0/dummy_{i+1}/data'}}, 
                  meta=dict()))

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

test_fnc(dict(soe=['orchestrator/start', 'lang/getPos_0', 'measure/schwefelFunction_0', 'analysis/dummy_0', 'ml/activeLearning_0'], 
            params={'start': {'collectionkey' : f'substrate_{substrate}'},
                    'getPos_0': {},
                    'schwefelFunction_0': {'x':dx0,'y':dy0},
                    'dummy_0': {'address':json.dumps([f'experiment_0:0/schwefelFunction_0/parameters/x',
                                                      f'experiment_0:0/schwefelFunction_0/parameters/y',
                                                      f'experiment_0:0/schwefelFunction_0/data/key_y'])},
                    'activeLearning_0': {'name': 'sdc_4', 'num': int(1), 'query': query, 'address':f'experiment_0:0/dummy_0/data'}},
            meta=dict()))

for i in range(n):
    test_fnc(dict(soe=[f'orchestrator/modify_{i}',f'lang/getPos_{i+1}', f'measure/schwefelFunction_{i+1}', f'analysis/dummy_{i+1}', f'ml/activeLearning_{i+1}'],
                  params={f'modify_{i}': {'addresses':[f'experiment_{i}:0/activeLearning_{i}/data/next_x',
                                                       f'experiment_{i}:0/activeLearning_{i}/data/next_y'],
                                            'pointers':[f'schwefelFunction_{i+1}/x',f'schwefelFunction_{i+1}/y']},
                            f'getPos_{i+1}': {},
                            f'schwefelFunction_{i+1}':{'x':'?','y':'?'},
                            f'dummy_{i+1}':{'address':json.dumps([f'experiment_{i+1}:0/schwefelFunction_{i+1}/parameters/x',
                                                                  f'experiment_{i+1}:0/schwefelFunction_{i+1}/parameters/y',
                                                                  f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/key_y'])},
                            f'activeLearning_{i+1}': {'name': 'sdc_4', 'num': int(i+1), 'query': query, 'address':f'experiment_{i+1}:0/dummy_{i+1}/data'}}, 
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
    test_fnc(dict(soe=[f'ml/activeLearningParallel_{i}',f'orchestrator/modify_{i}',f'lang:2/moveWaste_{i+1}', f'lang:2/RemoveDroplet_{i+1}',
                       f'lang:2/moveSample_{i+1}',f'lang:2/moveAbs_{i+1}',f'lang:2/moveDown_{i+1}',
                       f'measure:2/schwefelFunction_{i+1}',f'analysis/dummy_{i+1}'], 
                  params={f'activeLearningParallel_{i}':{'name': 'sdc_2', 'num': int(i+1), 'query': query, 'address':f'experiment_{i}:0/dummy_{i}/data/data'},
                            f'modify_{i}': {'addresses':[f'experiment_{i+1}:0/activeLearningParallel_{i}/data/data/next_x',
                                                         f'experiment_{i+1}:0/activeLearningParallel_{i}/data/data/next_y',
                                                         f'experiment_{i+1}:0/activeLearningParallel_{i}/data/data/next_x',
                                                         f'experiment_{i+1}:0/activeLearningParallel_{i}/data/data/next_y'],
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