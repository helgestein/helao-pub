import requests
import json
import numpy as np
import pandas as pd
import random
import math
import sys
import time
sys.path.append(r'../config')
sys.path.append('config')
from sdc_cyan import config
import matplotlib.pyplot as plt

def test_fnc(sequence, thread=0):
    server = 'orchestrator'
    action = 'addExperiment'
    params = dict(experiment=json.dumps(sequence),thread=thread)
    print("requesting")
    requests.post("http://{}:{}/{}/{}".format(
        config['servers']['orchestrator']['host'], 13390, server, action), params=params).json()

### Real wafer coordinates
random.seed(1)


substrate = 202
I = 0.02*1e-3*math.pi*0.045*0.045

x_values = np.arange(12.5, 50, 2.5)
y_values = np.arange(12.5, 50, 2.5)

grid = [(x, y) for y in y_values for x in x_values]

time.sleep(14400)

test_fnc(dict(soe=['orchestrator/start'], 
                params={'start': {'collectionkey' : f'substrate_{substrate}'}},
                meta=dict()))

test_fnc(dict(soe=['orchestrator/start'], 
                params={'start': {'collectionkey' : f'substrate_{substrate}'}},
                meta=dict()),1)

j=0
for i in list(range(0, 6)) + [14]:
#for i in range(30, 45):
    print(i)
    j+=1
    x=grid[i][0]
    y=grid[i][1]
    print(x,y)

    test_fnc(dict(soe=[f'dobot/moveHome_{0}', f'dobot/moveWaste_{0}', f'psd/pumpSimple_{0}', f'psd/pumpMix_{0}', 
                    f'force/read_{0}', f'dobot/removeDrop_{0}', f'dobot/removeDrop_{1}', f'dobot/removeDrop_{2}',  f'psd/pumpSimple_{1}',
                        f'dobot/moveSample_{0}', f'dobot/moveSample_{1}', f'dobot/moveDown_{0}', f'psd/pumpSimple_{2}', f'psd/pumpSimple_{3}',
                        f'psd/pumpSimple_{4}', f'psd/pumpSimple_{5}', f'psd/pumpSimple_{6}', f'force/read_{1}', f'palmsens/measure_{0}',
                        f'palmsens/measure_{1}', f'palmsens/measure_{2}', f'palmsens/measure_{3}', f'palmsens/measure_{4}',
                        f'palmsens/measure_{5}', f'palmsens/measure_{6}', f'palmsens/measure_{7}', f'palmsens/measure_{8}',
                        f'palmsens/measure_{9}', f'palmsens/measure_{10}', f'palmsens/measure_{11}', f'palmsens/measure_{12}', f'palmsens/measure_{13}', 
                        f'psd/pumpSimple_{7}', f'dobot/moveJointRelative_{0}', f'psd/pumpSimple_{8}', f'psd/pumpSimple_{9}', 
                        f'dobot/moveJointRelative_{1}', f'dobot/moveWaste_{1}', f'psd/pumpMix_{1}', f'dobot/removeDrop_{3}', f'dobot/moveHome_{1}'], 
                params={f'moveHome_{0}':{},
                        f'moveWaste_{0}':{'x': 0, 'y': 0, 'z': 0, 'r': 0},
                        f'pumpSimple_{0}': {'volume': 75, 'valve': 6, 'speed': 30, 'times': 1},
                        f'pumpMix_{0}': {'V1': 0, 'V2': 0, 'V3': 0, 'V4': 0, 'V5': 250, 'V6': 0, 'mix_speed': 35, 'mix': 0, 'vial_speed': 15, 'times': 1, 'cell': True},
                        f'read_{0}': {},
                        f'removeDrop_{0}': {'x': 1, 'y': 0.5, 'z': 0, 'r': 0},
                        f'removeDrop_{1}': {'x': -1, 'y': 0.5, 'z': 0, 'r': 0},
                        f'removeDrop_{2}': {'x': 0, 'y': 0.5, 'z': 0, 'r': 0},
                        f'pumpSimple_{1}': {'volume': 0, 'valve': 7, 'speed': 25, 'times': 1},
                        f'moveSample_{0}': {'x': x, 'y': y, 'z': 0, 'r': 0},
                        f'moveSample_{1}': {'x': x, 'y': y, 'z': -13.6, 'r': 0},
                        f'moveDown_{0}': {'dz': 0.05, 'steps': 50, 'maxForce': 200, 'threshold': 0.1},
                        f'pumpSimple_{2}': {'volume': 35, 'valve': 6, 'speed': 20, 'times': 1},
                        f'pumpSimple_{3}': {'volume': -30, 'valve': 7, 'speed': 20, 'times': 1},
                        f'pumpSimple_{4}': {'volume': 35, 'valve': 6, 'speed': 20, 'times': 1},
                        f'pumpSimple_{5}': {'volume': -30, 'valve': 7, 'speed': 20, 'times': 1},
                        f'pumpSimple_{6}': {'volume': 40, 'valve': 6, 'speed': 20, 'times': 1},
                        f'read_{1}': {},
                        f'measure_{0}': {'method': 'chronopotentiometry',
                                            'parameters': json.dumps({
                                            'i': 0.51e-9,               # Current in Amps
                                            't_interval': 0.1,       # IntervalTime
                                            't_run': 0.1,            # RunTime
                                            }),
                                        'filename': 'substrate_{}_pulse_{}_{}'.format(substrate, i, 1),
                                        'substrate': substrate,
                                        'id': i,
                                        'experiment': 10},
                        f'measure_{1}':{'method': 'open_circuit_potentiometry',
                                        'parameters': json.dumps({'t_run': 60.0, 't_interval': 0.5}),
                                        'filename': 'substrate_{}_ocp_{}_{}'.format(substrate, i, 1),
                                        'substrate': substrate,
                                        'id': i,
                                        'experiment': 1},
                        f'measure_{2}':{'method': 'potentiostatic_impedance_spectroscopy',
                                            'parameters': json.dumps({
                                                "e_dc": "None",                 # DC potential
                                                "e_ac": 0.01,                # AC potential (10 mV/s)
                                                "n_frequencies": int(10*7+1),         # Number of frequencies
                                                "max_frequency": 1e6,        # Maximum frequency
                                                "min_frequency": 1e-1,        # Minimum frequency
                                                "meas_vs_ocp_true": 0,       # Measure vs OCP
                                                "t_max_ocp": 30.0,           # Maximum time OCP stabilization
                                                "stability_criterion": 0.001 # Stability criterion in mV/s
                                                }),
                                            'filename': 'substrate_{}_peis_{}_{}'.format(substrate, i, 1),
                                            'substrate': substrate,
                                            'id': i,
                                            'experiment': 1},
                        f'measure_{3}':{'method': 'cyclic_voltammetry',
                                        'parameters': json.dumps({"equilibration_time": 10,  # Equilibration time in seconds
                                                                "e_begin": 0.8,          # Begin potential in volts
                                                                "e_vtx1": 1.4,           # Vertex 1 potential in volts
                                                                "e_vtx2": -0.4,            # Vertex 2 potential in volts
                                                                "e_step": 0.005,           # Step potential in volts
                                                                "scan_rate": 0.05,         # Scan rate in V/s
                                                                "n_scans": 3              # Number of scans
                                                                }),
                                        'filename': 'substrate_{}_cv_{}_{}'.format(substrate, i, 1),
                                        'substrate': substrate,
                                        'id': i,
                                        'experiment': 1},
                        f'measure_{4}':{'method': 'open_circuit_potentiometry',
                                        'parameters': json.dumps({'t_run': 180.0, 't_interval': 0.5}),
                                        'filename': 'substrate_{}_ocp_{}_{}'.format(substrate, i, 2),
                                        'substrate': substrate,
                                        'id': i,
                                        'experiment': 2},
                        f'measure_{5}':{'method': 'potentiostatic_impedance_spectroscopy',
                                            'parameters': json.dumps({
                                                "e_dc": "None",                 # DC potential
                                                "e_ac": 0.01,                # AC potential (10 mV/s)
                                                "n_frequencies": int(10*7+1),         # Number of frequencies
                                                "max_frequency": 1e6,        # Maximum frequency
                                                "min_frequency": 1e-1,        # Minimum frequency
                                                "meas_vs_ocp_true": 0,       # Measure vs OCP
                                                "t_max_ocp": 30.0,           # Maximum time OCP stabilization
                                                "stability_criterion": 0.001 # Stability criterion in mV/s
                                                }),
                                            'filename': 'substrate_{}_peis_{}_{}'.format(substrate, i, 2),
                                            'substrate': substrate,
                                            'id': i,
                                            'experiment': 2},
                        f'measure_{6}': {'method': 'chronopotentiometry',
                                                'parameters': json.dumps({
                                                'i': I,               # Current in Amps
                                                't_interval': 0.2,       # IntervalTime
                                                't_run': 3600.0,            # RunTime
                                                'e_max': 1.2,            # LimitMaxValue
                                                'e_max_bool': True,     # UseMaxValue
                                                'e_min': -0.2,           # LimitMinValue
                                                'e_min_bool': False      # UseMinValue
                                                }),
                                            'filename': 'substrate_{}_charge_{}_{}'.format(substrate, i, 0),
                                            'substrate': substrate,
                                            'id': i,
                                            'experiment': 0},
                        f'measure_{7}': {'method': 'chronopotentiometry',
                                                'parameters': json.dumps({
                                                'i': -I,               # Current in Amps
                                                't_interval': 0.2,       # IntervalTime
                                                't_run': 3600.0,         # RunTime
                                                'e_max': 1.2,            # LimitMaxValue
                                                'e_max_bool': False,     # UseMaxValue
                                                'e_min': -0.2,           # LimitMinValue
                                                'e_min_bool': True      # UseMinValue}
                                                }),
                                            'filename': 'substrate_{}_discharge_{}_{}'.format(substrate, i, 0),
                                            'substrate': substrate,
                                            'id': i,
                                            'experiment': 0},
                        f'measure_{8}': {'method': 'chronopotentiometry',
                                                'parameters': json.dumps({
                                                'i': I,               # Current in Amps
                                                't_interval': 0.2,       # IntervalTime
                                                't_run': 3600.0,         # RunTime
                                                'e_max': 1.2,            # LimitMaxValue
                                                'e_max_bool': True,     # UseMaxValue
                                                'e_min': -0.2,           # LimitMinValue
                                                'e_min_bool': False      # UseMinValue}
                                                }),
                                            'filename': 'substrate_{}_charge_{}_{}'.format(substrate, i, 1),
                                            'substrate': substrate,
                                            'id': i,
                                            'experiment': 1},
                        f'measure_{9}': {'method': 'chronopotentiometry',
                                                'parameters': json.dumps({
                                                'i': -I,               # Current in Amps
                                                't_interval': 0.2,       # IntervalTime
                                                't_run': 3600.0,         # RunTime
                                                'e_max': 1.2,            # LimitMaxValue
                                                'e_max_bool': False,     # UseMaxValue
                                                'e_min': -0.2,           # LimitMinValue
                                                'e_min_bool': True      # UseMinValue}
                                                }),
                                            'filename': 'substrate_{}_discharge_{}_{}'.format(substrate, i, 1),
                                            'substrate': substrate,
                                            'id': i,
                                            'experiment': 1},
                        f'measure_{10}': {'method': 'chronopotentiometry',
                                                'parameters': json.dumps({
                                                'i': I,               # Current in Amps
                                                't_interval': 0.2,       # IntervalTime
                                                't_run': 3600.0,         # RunTime
                                                'e_max': 1.2,            # LimitMaxValue
                                                'e_max_bool': True,     # UseMaxValue
                                                'e_min': -0.2,           # LimitMinValue
                                                'e_min_bool': False      # UseMinValue}
                                                }),
                                            'filename': 'substrate_{}_charge_{}_{}'.format(substrate, i, 2),
                                            'substrate': substrate,
                                            'id': i,
                                            'experiment': 2},
                        f'measure_{11}': {'method': 'chronopotentiometry',
                                                'parameters': json.dumps({
                                                'i': -I,               # Current in Amps
                                                't_interval': 0.2,       # IntervalTime
                                                't_run': 3600.0,         # RunTime
                                                'e_max': 1.2,            # LimitMaxValue
                                                'e_max_bool': False,     # UseMaxValue
                                                'e_min': -0.2,           # LimitMinValue
                                                'e_min_bool': True      # UseMinValue}
                                                }),
                                            'filename': 'substrate_{}_discharge_{}_{}'.format(substrate, i, 2),
                                            'substrate': substrate,
                                            'id': i,
                                            'experiment': 2},
                        f'measure_{12}':{'method': 'open_circuit_potentiometry',
                                        'parameters': json.dumps({'t_run': 180.0, 't_interval': 0.5}),
                                        'filename': 'substrate_{}_ocp_{}_{}'.format(substrate, i, 3),
                                        'substrate': substrate,
                                        'id': i,
                                        'experiment': 3},
                        f'measure_{13}':{'method': 'potentiostatic_impedance_spectroscopy',
                                            'parameters': json.dumps({
                                                "e_dc": "None",                 # DC potential
                                                "e_ac": 0.01,                # AC potential (10 mV/s)
                                                "n_frequencies": int(10*7+1),         # Number of frequencies
                                                "max_frequency": 1e6,        # Maximum frequency
                                                "min_frequency": 1e-1,        # Minimum frequency
                                                "meas_vs_ocp_true": 0,       # Measure vs OCP
                                                "t_max_ocp": 30.0,           # Maximum time OCP stabilization
                                                "stability_criterion": 0.001 # Stability criterion in mV/s
                                                }),
                                            'filename': 'substrate_{}_peis_{}_{}'.format(substrate, i, 3),
                                            'substrate': substrate,
                                            'id': i,
                                            'experiment': 3},
                        f'pumpSimple_{7}': {'volume': -125, 'valve': 7, 'speed': 20, 'times': 1},
                        f'moveJointRelative_{0}':{'x': 0, 'y':0, 'z': 0.4, 'r': 0},
                        f'pumpSimple_{8}': {'volume': -125, 'valve': 7, 'speed': 30, 'times': 1},
                        f'pumpSimple_{9}': {'volume': -100, 'valve': 7, 'speed': 20, 'times': 1},
                        f'moveJointRelative_{1}':{'x': 0, 'y':0, 'z': 2, 'r': 0},
                        f'moveWaste_{1}':{'x': 0, 'y': 0, 'z': 0, 'r': 0},
                        f'pumpMix_{1}': {'V1': 0, 'V2': 0, 'V3': 0, 'V4': 0, 'V5': 75, 'V6': 0, 'mix_speed': 20, 'mix': 0, 'vial_speed': 12, 'times': 1, 'cell': True},
                        f'removeDrop_{3}': {'x': 0, 'y': 0, 'z': 0, 'r': 0},                                    
                        f'moveHome_{1}':{}
                        },
                meta=dict()))

    test_fnc(dict(soe=[f'orchestrator/wait_{0}']+[f'dobot/moveJointRelative_{i}' for i in range(50)], 
                    params={f'wait_{0}': {'addresses':f'experiment_{j}:0/pumpSimple_{8}'},
                            **{f'moveJointRelative_{i}': {'x': 0, 'y': 0, 'z': 0.02, 'r': 0} for i in range(50)}
                            },
                    meta=dict()),1)

    
    
### emergency droplet remove

test_fnc(dict(soe=['orchestrator/start', f'psd/pumpSimple_{7}', f'dobot/moveJointRelative_{0}', f'psd/pumpSimple_{8}', f'psd/pumpSimple_{9}', 
                   f'dobot/moveJointRelative_{1}', f'dobot/moveWaste_{1}', f'psd/pumpMix_{1}', f'dobot/removeDrop_{3}', f'dobot/moveHome_{1}'],
            params={'start': {'collectionkey' : f'substrate_{substrate}'},
                    f'pumpSimple_{7}': {'volume': -100, 'valve': 7, 'speed': 20, 'times': 1},
                    f'moveJointRelative_{0}':{'x': 0, 'y':0, 'z': 0.4, 'r': 0},
                    f'pumpSimple_{8}': {'volume': -100, 'valve': 7, 'speed': 30, 'times': 1},
                    f'pumpSimple_{9}': {'volume': -100, 'valve': 7, 'speed': 20, 'times': 1},
                    f'moveJointRelative_{1}':{'x': 0, 'y':0, 'z': 2, 'r': 0},
                    f'moveWaste_{1}':{'x': 0, 'y': 0, 'z': 0, 'r': 0},
                    f'pumpMix_{1}': {'V1': 200, 'V2': 0, 'V3': 0, 'V4': 0, 'V5': 0, 'V6': 0, 'mix_speed': 20, 'mix': 0, 'vial_speed': 12, 'times': 2, 'cell': True},
                    f'removeDrop_{3}': {'x': 0, 'y': 0, 'z': 0, 'r': 0},                                    
                    f'moveHome_{1}':{}
                    },
            meta=dict()))

test_fnc(dict(soe=['orchestrator/start'], 
                params={'start': {'collectionkey' : f'substrate_{substrate}'}},
                meta=dict()),1)

test_fnc(dict(soe=[f'orchestrator/wait_{0}']+[f'dobot/moveJointRelative_{i}' for i in range(75)], 
                params={f'wait_{0}': {'addresses':f'experiment_{0}:0/pumpSimple_{8}'},
                        **{f'moveJointRelative_{i}': {'x': 0, 'y': 0, 'z': 0.02, 'r': 0} for i in range(75)}
                        },
                meta=dict()),1)