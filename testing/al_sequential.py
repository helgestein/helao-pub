import requests
import json
import numpy as np
import random
import sys
sys.path.append(r'../config')
sys.path.append('config')
from sdc_2 import config


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
# real run
x_grid, y_grid = np.meshgrid([2.5 * i for i in range(21)], [2.5 * i for i in range(21)])

x, y = x_grid.flatten(), y_grid.flatten()
x_query = np.array([[i, j] for i, j in zip(x, y)])
first_arbitary_choice = random.choice(x_query)
dx0, dy0 = first_arbitary_choice[0], first_arbitary_choice[1]
y_query = [schwefel_function(x[0], x[1])for x in x_query]
z_con = np.array(y_query).reshape((len(x_grid), len(y_grid)))
query = json.dumps({'x_query': x_query.tolist(), 'y_query': y_query, 'z_con': z_con.tolist()})  
dz = config['lang:2']['safe_sample_pos'][2]


n = 100
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