# analysis is the bridge between data transfering. Adresses should go there.
from sdc_2 import config
import requests
import json
import numpy as np
import random
import sys
sys.path.append('config')
#from pctest_config import config


def test_fnc(sequence, thread=0):
    server = 'orchestrator'
    action = 'addExperiment'
    params = dict(experiment=json.dumps(sequence), thread=thread)
    print("requesting")
    requests.post("http://{}:{}/{}/{}".format(
        config['servers']['orchestrator']['host'], 13380, server, action), params=params).json()


def schwefel_function(x, y):
    comp = np.array([x, y])
    sch_comp = 1000 * np.array(comp) - 500
    result = 0
    for index, element in enumerate(sch_comp):
        result += - element * np.sin(np.sqrt(np.abs(element)))
    result = (-result) / 1000
    return result


# real run
x_grid, y_grid = np.meshgrid(
    [2.5 * i for i in range(20)], [2.5 * i for i in range(20)])

x, y = x_grid.flatten(), y_grid.flatten()
x_query = np.array([[i, j] for i, j in zip(x, y)])
arbitary_choices = random.choices(x_query, k=2)
dx0, dy0, dx1, dy1 = arbitary_choices[0][0], arbitary_choices[0][1], arbitary_choices[1][0], arbitary_choices[1][1]

#dx0, dy0 = first_arbitary_choice[0], first_arbitary_choice[1]
y_query = [schwefel_function(x[0], x[1])for x in x_query]
z_con = np.array(y_query).reshape((len(x_grid), len(y_grid)))
# , 'x_grid': x_grid.tolist(), 'y_grid':y_grid.tolist(), 'z_con':z_con.tolist()
query = json.dumps({'x_query': x_query.tolist(), 'y_query': y_query,
                    'x_grid': x_grid.tolist(), 'y_grid': y_grid.tolist(), 'z_con': z_con.tolist()})
dz = config['lang:2']['safe_sample_pos'][2]
inital_height = 5
num_step = 10
fume_max_force = 10
num_sampling = 40

test_fnc(dict(soe=['orchestrator/start', 'lang:1/moveWaste_0', 'lang:1/RemoveDroplet_0', 'lang:1/moveSample_0', 'lang:1/moveAbs_0', 'lang:1/moveRel_0',
                   'lang:1/moveDown_0', 'measure:1/schwefelFunction_0', 'analysis/dummy_0', 'ml/activeLearningParallel_0'],
              params={'start': {'collectionkey': 'al_parallel'}, 'moveWaste_0': {'x': 0, 'y': 0, 'z': 0},
                      'RemoveDroplet_0': {'x': 0, 'y': 0, 'z': 0},
                      'moveSample_0': {'x': 0, 'y': 0, 'z': 0},
                      'moveAbs_0': {'dx': dx0, 'dy': dy0, 'dz': dz},
                      'moveRel_0': {'dx': 0, 'dy': 0, 'dz': inital_height},
                      'moveDown_0': {'dz': 0.05, 'steps': num_step, 'maxForce': fume_max_force, 'threshold': 0.13},
                      'schwefelFunction_0': {'x': dx0, 'y': dy0},
                      'dummy_0': {'x_address': 'experiment_0:0/schwefelFunction_0/data/parameters/x',
                                  'y_address': 'experiment_0:0/schwefelFunction_0/data/parameters/y',
                                  'schwefel_address': 'experiment_0:0/schwefelFunction_0/data/data/key_y'},
                      'activeLearningParallel_0': {'name': 'sdc_1', 'num': 0, 'query': query, 'address': f'experiment_0:0/dummy_0/data/data'}}, meta=dict()))

for i in range(num_sampling):
    test_fnc(dict(soe=[f'orchestrator/modify_{i}', f'lang:1/moveWaste_{i+1}', f'lang:1/RemoveDroplet_{i+1}', f'lang:1/moveSample_{i+1}',
                       f'lang:1/moveAbs_{i+1}', f'lang:1/moveRel_{i+1}', f'lang:1/moveDown_{i+1}', f'measure:1/schwefelFunction_{i+1}', f'analysis/dummy_{i+1}', f'ml/activeLearningParallel_{i+1}'],
                  params={
        f'modify_{i}': {'addresses': [f'experiment_{i}:2/activeLearningParallel_{2*i}/data/data/next_x',
                                      f'experiment_{i}:2/activeLearningParallel_{2*i}/data/data/next_y'],
                        'pointers': [f'schwefelFunction_{i+1}/x', f'schwefelFunction_{i+1}/y', f'moveAbs_{i+1}/dx', f'moveAbs_{i+1}/dy']},
        f'moveWaste_{i+1}': {'x': 0, 'y': 0, 'z': 0},
        f'RemoveDroplet_{i+1}': {'x': 0, 'y': 0, 'z': 0},
        f'moveSample_{i+1}': {'x': 0, 'y': 0, 'z': 0},
        f'moveAbs_{i+1}': {'dx': '?', 'dy': '?', 'dz': dz},
        f'moveRel_{i+1}': {'dx': 0, 'dy': 0, 'dz': inital_height},
        f'moveDown_{i+1}': {'dz': 0.05, 'steps': num_step, 'maxForce': fume_max_force, 'threshold': 0.13},
        f'schwefelFunction_{i+1}': {'x': '?', 'y': '?'},
        f'dummy_{i+1}': {'x_address': f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/parameters/x', 'y_address': f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/parameters/y',
                         'schwefel_address': f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/data/key_y'}
        f'activeLearningParallel_{i+1}': {'name': 'sdc_1', 'num': int(i+1), 'query': query, 'address': f'experiment_{i+1}:0/dummy_{i+1}/data/data'}}, meta=dict()))

test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))


# second SDC , will get the modified point after AL given initialized input from sdc_1
test_fnc(dict(soe=['lang:2/moveWaste_0', 'lang:2/RemoveDroplet_0', 'lang:2/moveSample_0', 'lang:2/moveAbs_0', 'lang:2/moveRel_0',
                   'lang:2/moveDown_0', 'measure:2/schwefelFunction_0', 'analysis/dummy_0', 'ml/activeLearningParallel_0'],
              params={'moveWaste_0': {'x': 0, 'y': 0, 'z': 0},
                      'RemoveDroplet_0': {'x': 0, 'y': 0, 'z': 0},
                      'moveSample_0': {'x': 0, 'y': 0, 'z': 0},
                      'moveAbs_0': {'dx': dx2, 'dy': dy2, 'dz': dz},
                      'moveRel_0': {'dx': 0, 'dy': 0, 'dz': inital_height},
                      'moveDown_0': {'dz': 0.05, 'steps': num_step, 'maxForce': 1.4, 'threshold': 0.13},
                      'schwefelFunction_0': {'x': dx2, 'y': dy2},
                      'dummy_0': {'x_address': 'experiment_0:0/schwefelFunction_0/data/parameters/x',
                                  'y_address': 'experiment_0:0/schwefelFunction_0/data/parameters/y',
                                  'schwefel_address': 'experiment_0:0/schwefelFunction_0/data/data/key_y'},
                      'activeLearningParallel_0': {'name': 'sdc_2', 'num': 0, 'query': query, 'address': f'experiment_0:0/dummy_0/data/data'}}, meta=dict()), 1)

for i in range(num_sampling-1):
    test_fnc(dict(soe=[f'orchestrator/wait_{i+1}', f'orchestrator/modify_{i+1}', f'lang:2/moveWaste_{i+1}', f'lang:2/RemoveDroplet_{i+1}', f'lang:2/moveSample_{i+1}',
                       f'lang:2/moveAbs_{i+1}', f'lang:2/moveRel_{i+1}', f'lang:2/moveDown_{i+1}', f'measure:2/schwefelFunction_{i+1}', f'analysis/dummy_{i+1}', f'ml/activeLearningParallel_{i+1}'],
                  params={f'wait_{i+1}': {'addresses': f'experiment_{i+1}:2/activeLearningParallel_{i+1}'},
                          f'modify_{i+1}': {'addresses': [f'experiment_{i+1}:2/activeLearningParallel_{i+1}/data/data/next_x_2',
                                                          f'experiment_{i+1}:2/activeLearningParallel_{i+1}/data/data/next_y_2'],
                                            'pointers': [f'schwefelFunction_{i+1}/x', f'schwefelFunction_{i+1}/y', f'moveAbs_{i+1}/dx', f'moveAbs_{i+1}/dy']},
                          f'moveWaste_{i+1}': {'x': 0, 'y': 0, 'z': 0},
                          f'RemoveDroplet_{i+1}': {'x': 0, 'y': 0, 'z': 0},
                          f'moveSample_{i+1}': {'x': 0, 'y': 0, 'z': 0},
                          f'moveAbs_{i+1}': {'dx': '?', 'dy': '?', 'dz': dz},
                          f'moveRel_{i+1}': {'dx': 0, 'dy': 0, 'dz': inital_height},
                          f'moveDown_{i+1}': {'dz': 0.05, 'steps': num_step, 'maxForce': 1.4, 'threshold': 0.13},
                          f'schwefelFunction_{i+1}': {'x': '?', 'y': '?'},
                          f'dummy_{i+1}': {'x_address': f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/parameters/x', 'y_address': f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/parameters/y', 'schwefel_address': f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/data/key_y'},
                          f'activeLearningParallel_{i+1}': {'name': 'sdc_2', 'num': int(i+1), 'query': query, 'address': f'experiment_{i+1}:0/dummy_{i+1}/data/data'}}, meta=dict()), 1)

test_fnc(dict(soe=['orchestrator/finish'],
              params={'finish': None}, meta={}), 1)
