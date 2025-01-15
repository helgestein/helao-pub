import requests
import json
import numpy as np
import random
import sys
from datetime import datetime
sys.path.append(r'../config')
sys.path.append('config')
from sdc_4 import config

def test_fnc(sequence,thread=0):
    server = 'orchestrator'
    action = 'addExperiment'
    params = dict(experiment=json.dumps(sequence),thread=thread)
    print("requesting")
    requests.post("http://{}:{}/{}/{}".format(
        config['servers']['orchestrator']['host'], 13390, server, action), params=params).json()
    
def schwefel_function(x, y):
    comp = np.array([x, y])
    sch_comp = 20 * np.array(comp) - 500
    result = 0
    for index, element in enumerate(sch_comp):
        #print(f"index is {index} and element is {element}")
        result += - element * np.sin(np.sqrt(np.abs(element)))
    result = (-result) / 1000
    return result

# real run for fun
x_grid, y_grid = np.meshgrid([2.5 * i for i in range(5)], [2.5 * i for i in range(5)])
x, y = x_grid.flatten(), y_grid.flatten()
x_query = np.array([[i, j] for i, j in zip(x, y)])
first_arbitary_choice = random.choice(x_query)
dx0, dy0 = first_arbitary_choice[0], first_arbitary_choice[1]
y_query = [schwefel_function(x[0], x[1])for x in x_query]
z_con = np.array(y_query).reshape((len(x_grid), len(y_grid)))
query = json.dumps({'x_query': x_query.tolist(), 'y_query': y_query, 'z_con': z_con.tolist()})

substrate = -99999

test_fnc(dict(soe=['orchestrator/start', 'measure/schwefelFunction_0', 'analysis/dummy0_0'],
             params={'start': {'collectionkey' : f'substrate_{substrate}'},
                     'schwefelFunction_0':{'x':dx0,'y':dy0},
                     'dummy0_0':{'address':json.dumps(['experiment_0:0/schwefelFunction_0/parameters/x',
                                            'experiment_0:0/schwefelFunction_0/parameters/y',
                                            'experiment_0:0/schwefelFunction_0/data/key_y'])}},
             meta=dict(substrate=substrate, start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))))

n = 1
for i in range(n):
    test_fnc(dict(soe=[f'ml/activeLearningParallel_{i}', f'orchestrator/modify_{i}', f'measure/schwefelFunction_{i+1}', f'analysis/dummy_{i+1}'], 
                params={f'activeLearningParallel_{i}':{'name': 'sdc_4', 'num': int(i+1), 'query': query, 'address':f'experiment_{i}:0/dummy_{i}/data'},
                        f'modify_{i}': {'addresses':[f'experiment_{i+1}:0/activeLearningParallel_{i}/data/next_x',
                                                         f'experiment_{i+1}:0/activeLearningParallel_{i}/data/next_y'],
                                            'pointers':[f'schwefelFunction_{i+1}/x',f'schwefelFunction_{i+1}/y']},
                        f'schwefelFunction_{i+1}':{'x':'?','y':'?'},
                        f'dummy_{i+1}':{'x_address':f'experiment_{i+1}:0/schwefelFunction_{i+1}/parameters/x',
                                        'y_address':f'experiment_{i+1}:0/schwefelFunction_{i+1}/parameters/y',
                                        'schwefel_address':f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/key_y'}},
                meta=dict(substrate=substrate, start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))))
    
test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta=dict(substrate=substrate, start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))))


###
i=0
test_fnc(dict(soe=['orchestrator/start', 'measure/schwefelFunction_0', 'analysis/dummy0_0', f'ml/activeLearningParallel_{0}'],
             params={'start': {'collectionkey' : f'substrate_{substrate}'},
                     'schwefelFunction_0':{'x':dx0,'y':dy0},
                     'dummy0_0':{'address':json.dumps(['experiment_0:0/schwefelFunction_0/parameters/x',
                                            'experiment_0:0/schwefelFunction_0/parameters/y',
                                            'experiment_0:0/schwefelFunction_0/data/key_y'])},
                     'activeLearningParallel_0':{'name': 'sdc_4', 'num': int(i+1), 'query': query, 'address':f'experiment_{i}:0/dummy0_{i}/data'}},
             meta=dict(substrate=substrate, start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))))