import requests
import json
import numpy as np
import pandas as pd
import random
import math
import sys
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

# -20 for a small tip
# -50 for a large tip

substrate = -201

x_values = np.arange(12.5, 50, 2.5)
y_values = np.arange(12.5, 50, 2.5)

grid = [(x, y) for y in y_values for x in x_values]

### prussian blue electrodeposition test
i=6
n=20
x=grid[i][0]
y=grid[i][1]

charging = {}
for j in range(n):
    charging[f'measure_{3+2*j}'] = {
        'method': 'chronoamperometry',
        'parameters': json.dumps({
            "e_applied": 0.1,  # Applied potential in volts
            "interval_time": 0.2,  # Interval time in seconds
            "run_time": 5.0,  # Total run time in seconds
        }),
        'filename': 'substrate_{}_ca_{}_{}'.format(substrate, i, j+1),
        'substrate': substrate,
        'id': i,
        'experiment': j+1
    }
    charging[f'measure_{4+2*j}'] = {
        'method': 'open_circuit_potentiometry',
        'parameters': json.dumps({'t_run': 5.0, 't_interval': 0.2}),
        'filename': 'substrate_{}_ocp_{}_{}'.format(substrate, i, j+1),
        'substrate': substrate,
        'id': i,
        'experiment': j+1
    }

test_fnc(dict(soe=['orchestrator/start', f'dobot/moveHome_{0}', f'dobot/moveWaste_{0}', f'psd/pumpSimple_{0}', f'psd/pumpMix_{0}', 
                f'force/read_{0}', f'dobot/removeDrop_{0}', f'dobot/removeDrop_{1}', f'dobot/removeDrop_{2}',  f'psd/pumpSimple_{1}',
                        f'dobot/moveSample_{0}', f'dobot/moveSample_{1}', f'dobot/moveDown_{0}', f'psd/pumpSimple_{2}', f'psd/pumpSimple_{3}',
                        f'psd/pumpSimple_{4}', f'psd/pumpSimple_{5}', f'psd/pumpSimple_{6}', f'force/read_{1}', f'palmsens/measure_{0}',
                        f'palmsens/measure_{1}', f'palmsens/measure_{2}']+[f'palmsens/measure_{3+i}' for i in range(n*2)]
                        +[f'psd/pumpSimple_{7}', f'dobot/moveJointRelative_{0}', f'psd/pumpSimple_{8}', f'psd/pumpSimple_{9}', 
                        f'dobot/moveJointRelative_{1}', f'dobot/moveWaste_{1}', f'psd/pumpMix_{1}', f'dobot/removeDrop_{3}', f'dobot/moveHome_{1}'], 
                params={'start': {'collectionkey' : f'substrate_{substrate}'},
                        f'moveHome_{0}':{},
                        f'moveWaste_{0}':{'x': 0, 'y': 0, 'z': 0, 'r': 0},
                        f'pumpSimple_{0}': {'volume': 100, 'valve': 1, 'speed': 25, 'times': 1},
                        f'pumpMix_{0}': {'V1': 0, 'V2': 100, 'V3': 0, 'V4': 100, 'V5': 0, 'V6': 0, 'mix_speed': 30, 'mix': 1, 'vial_speed': 15, 'times': 1, 'cell': True},
                        f'read_{0}': {},
                        f'removeDrop_{0}': {'x': 1, 'y': 0.5, 'z': 0, 'r': 0},
                        f'removeDrop_{1}': {'x': -1, 'y': 0.5, 'z': 0, 'r': 0},
                        f'removeDrop_{2}': {'x': 0, 'y': 0.5, 'z': 0, 'r': 0},
                        f'pumpSimple_{1}': {'volume': 0, 'valve': 7, 'speed': 25, 'times': 1},
                        f'moveSample_{0}': {'x': x, 'y': y, 'z': 0, 'r': 0},
                        f'moveSample_{1}': {'x': x, 'y': y, 'z': -13.6, 'r': 0},
                        f'moveDown_{0}': {'dz': 0.05, 'steps': 50, 'maxForce': 150, 'threshold': 0.1},
                        f'pumpSimple_{2}': {'volume': 25, 'valve': 8, 'speed': 25, 'times': 1},
                        f'pumpSimple_{3}': {'volume': -20, 'valve': 7, 'speed': 20, 'times': 1},
                        f'pumpSimple_{4}': {'volume': 25, 'valve': 8, 'speed': 20, 'times': 1},
                        f'pumpSimple_{5}': {'volume': -20, 'valve': 7, 'speed': 30, 'times': 1},
                        f'pumpSimple_{6}': {'volume': 30, 'valve': 8, 'speed': 30, 'times': 1},
                        f'read_{1}': {},
                        f'measure_{0}': {'method': 'chronopotentiometry',
                                            'parameters': json.dumps({
                                            'i': 0.51e-9,               # Current in Amps
                                            't_interval': 0.1,       # IntervalTime
                                            't_run': 0.1,            # RunTime
                                            }),
                                        'filename': 'substrate_{}_pulse_{}_{}'.format(substrate, i, 0),
                                        'substrate': substrate,
                                        'id': i,
                                        'experiment': 0},
                        f'measure_{1}':{'method': 'open_circuit_potentiometry',
                                        'parameters': json.dumps({'t_run': 60.0, 't_interval': 0.5}),
                                        'filename': 'substrate_{}_ocp_{}_{}'.format(substrate, i, 0),
                                        'substrate': substrate,
                                        'id': i,
                                        'experiment': 0},
                        f'measure_{2}':{'method': 'potentiostatic_impedance_spectroscopy',
                                        'parameters': json.dumps({
                                                "e_dc": "None",                 # DC potential
                                                "e_ac": 0.01,                # AC potential (10 mV/s)
                                                "n_frequencies": int(10*3+1),         # Number of frequencies
                                                "max_frequency": 1e5,        # Maximum frequency
                                                "min_frequency": 1e2,        # Minimum frequency
                                                "meas_vs_ocp_true": 0,       # Measure vs OCP
                                                "t_max_ocp": 30.0,           # Maximum time OCP stabilization
                                                "stability_criterion": 0.001 # Stability criterion in mV/s
                                                }),
                                        'filename': 'substrate_{}_peis_{}_{}'.format(substrate, i, 0),
                                        'substrate': substrate,
                                        'id': i,
                                        'experiment': 0},
                        **charging,
                        f'pumpSimple_{7}': {'volume': -75, 'valve': 7, 'speed': 20, 'times': 1},
                        f'moveJointRelative_{0}':{'x': 0, 'y':0, 'z': 0.4, 'r': 0},
                        f'pumpSimple_{8}': {'volume': -75, 'valve': 7, 'speed': 30, 'times': 1},
                        f'pumpSimple_{9}': {'volume': -100, 'valve': 7, 'speed': 15, 'times': 1},
                        f'moveJointRelative_{1}':{'x': 0, 'y':0, 'z': 2, 'r': 0},
                        f'moveWaste_{1}':{'x': 0, 'y': 0, 'z': 0, 'r': 0},
                        f'pumpMix_{1}': {'V1': 75, 'V2': 0, 'V3': 0, 'V4': 0, 'V5': 0, 'V6': 0, 'mix_speed': 20, 'mix': 3, 'vial_speed': 12, 'times': 3, 'cell': True},
                        f'removeDrop_{3}': {'x': 0, 'y': 0, 'z': 0, 'r': 0},                                    
                        f'moveHome_{1}':{}
                        },
                meta=dict()))

test_fnc(dict(soe=['orchestrator/start'], 
                params={'start': {'collectionkey' : f'substrate_{substrate}'}},
                meta=dict()),1)

test_fnc(dict(soe=[f'orchestrator/wait_{0}']+[f'dobot/moveJointRelative_{i}' for i in range(75)], 
                params={f'wait_{0}': {'addresses':f'experiment_{0}:0/pumpSimple_{8}'},
                        **{f'moveJointRelative_{i}': {'x': 0, 'y': 0, 'z': 0.01, 'r': 0} for i in range(75)}
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







test_fnc(dict(soe=[f'palmsens/measure_{1}', f'palmsens/measure_{2}', f'palmsens/measure_{3}', f'psd/pumpSimple_{6}', f'dobot/moveJointRelative_{0}', 
                   f'psd/pumpSimple_{7}', f'dobot/moveJointRelative_{1}', f'psd/pumpSimple_{8}', f'dobot/moveJointRelative_{2}', f'psd/pumpSimple_{9}', 
                   f'dobot/moveJointRelative_{3}', f'dobot/moveWaste_{1}', f'psd/pumpSimple_{10}', f'dobot/moveHome_{1}'], 
            params={f'measure_{1}':{'method': 'potentiostatic_impedance_spectroscopy',
                                        'parameters': json.dumps({
                                            "e_dc": 0.0,                 # DC potential
                                            "e_ac": 0.01,                # AC potential (10 mV/s)
                                            "n_frequencies": int(10*5+1),         # Number of frequencies
                                            "max_frequency": 1e6,        # Maximum frequency
                                            "min_frequency": 1e1,        # Minimum frequency
                                            "meas_vs_ocp_true": 1,       # Measure vs OCP
                                            "t_max_ocp": 30.0,           # Maximum time OCP stabilization
                                            "stability_criterion": 0.001 # Stability criterion in mV/s
                                            }),
                                        'filename': 'substrate_{}_peis_{}_{}'.format(substrate, id0, 0),
                                        'substrate': substrate,
                                        'id': 0,
                                        'experiment': 0},
                    f'measure_{2}':{'method': 'cyclic_voltammetry',
                                    'parameters': json.dumps({"equilibration_time": 30,  # Equilibration time in seconds
                                                            "e_begin": 0.5,          # Begin potential in volts
                                                            "e_vtx1": 0.0,           # Vertex 1 potential in volts
                                                            "e_vtx2": 0.5,            # Vertex 2 potential in volts
                                                            "e_step": 0.005,           # Step potential in volts
                                                            "scan_rate": 0.05,         # Scan rate in V/s
                                                            "n_scans": 3              # Number of scans
                                                            }),
                                    'filename': 'substrate_{}_cv_{}_{}'.format(substrate, id0, 0),
                                    'substrate': substrate,
                                    'id': id0,
                                    'experiment': 0},
                    f'measure_{3}':{'method': 'potentiostatic_impedance_spectroscopy',
                                        'parameters': json.dumps({
                                            "e_dc": 0.0,                 # DC potential
                                            "e_ac": 0.01,                # AC potential (10 mV/s)
                                            "n_frequencies": int(10*5+1),         # Number of frequencies
                                            "max_frequency": 1e6,        # Maximum frequency
                                            "min_frequency": 1e1,        # Minimum frequency
                                            "meas_vs_ocp_true": 1,       # Measure vs OCP
                                            "t_max_ocp": 30.0,           # Maximum time OCP stabilization
                                            "stability_criterion": 0.001 # Stability criterion in mV/s
                                            }),
                                        'filename': 'substrate_{}_peis_{}_{}'.format(substrate, id0, 1),
                                        'substrate': substrate,
                                        'id': 0,
                                        'experiment': 1},
                    f'pumpSimple_{6}': {'volume': -200, 'valve': 7, 'speed': 20, 'times': 1},
                    f'moveJointRelative_{0}':{'x': 0, 'y':0, 'z': 0.5, 'r': 0},
                    f'pumpSimple_{7}': {'volume': -100, 'valve': 7, 'speed': 20, 'times': 1},
                    f'moveJointRelative_{1}':{'x': 0, 'y':0, 'z': 0.25, 'r': 0},
                    f'pumpSimple_{8}': {'volume': -100, 'valve': 7, 'speed': 30, 'times': 1},
                    f'moveJointRelative_{2}':{'x': 0, 'y':0, 'z': 0.25, 'r': 0},
                    f'pumpSimple_{9}': {'volume': -100, 'valve': 7, 'speed': 35, 'times': 1},
                    f'moveJointRelative_{3}':{'x': 0, 'y':0, 'z': 2.0, 'r': 0},
                    f'moveWaste_{1}':{'x': 0, 'y': 0, 'z': 0, 'r': 0},
                    f'pumpSimple_{10}': {'volume': 200, 'valve': 3, 'speed': 25, 'times': 1},                                    
                    f'moveHome_{1}':{}
                    },
            meta=dict()))


test_fnc(dict(soe=[f'psd/pumpSimple_{8}'], 
            params={f'pumpSimple_{8}': {'volume': 200, 'valve': 7, 'speed': 25, 'times': 1}
                    },
            meta=dict()))

test_fnc(dict(soe=[f'psd/pumpSimple_{8}'], 
            params={f'pumpSimple_{8}': {'volume': -100, 'valve': 7, 'speed': 25, 'times': 1}
                    },
            meta=dict()))

test_fnc(dict(soe=[f'orchestrator/wait_{0}']+[f'dobot/moveJointRelative_{i}' for i in range(50)], 
                params={f'wait_{0}': {'addresses':f'experiment_{2}:0/pumpSimple_{8}'},
                        **{f'moveJointRelative_{i}': {'x': 0, 'y': 0, 'z': 0.02, 'r': 0} for i in range(50)}
                        },
                meta=dict()),1)

test_fnc(dict(soe=[f'dobot/moveWaste_{1}', f'psd/pumpSimple_{10}', f'dobot/moveHome_{1}'], 
            params={f'moveWaste_{1}':{'x': 0, 'y': 0, 'z': 0, 'r': 0},
                    f'pumpSimple_{10}': {'volume': 200, 'speed': 25, 'times': 1},                                    
                    f'moveHome_{1}':{}
                    },
            meta=dict()),1)

test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))

test_fnc(dict(soe=['orchestrator/start'], 
                params={'start': {'collectionkey' : f'substrate_{substrate}'}},
                meta=dict()))

test_fnc(dict(soe=[f'psd/pumpSimple_{8}', f'dobot/moveJointRelative_{2}', f'psd/pumpSimple_{9}', f'dobot/moveJointRelative_{3}', f'dobot/moveWaste_{1}', 
                    f'psd/pumpSimple_{10}', f'dobot/moveHome_{1}'], 
            params={f'pumpSimple_{8}': {'volume': -100, 'valve': 7, 'speed': 35, 'times': 1},
                    f'moveJointRelative_{2}':{'x': 0, 'y':0, 'z': 0.25, 'r': 0},
                    f'pumpSimple_{9}': {'volume': -100, 'valve': 7, 'speed': 35, 'times': 1},
                    f'moveJointRelative_{3}':{'x': 0, 'y':0, 'z': 2.0, 'r': 0},
                    f'moveWaste_{1}':{'x': 0, 'y': 0, 'z': 0, 'r': 0},
                    f'pumpSimple_{10}': {'volume': 200, 'speed': 25, 'times': 1},                                    
                    f'moveHome_{1}':{}
                    },
            meta=dict()))

test_fnc(dict(soe=['orchestrator/start', f'psd/pumpSimple_{6}', f'dobot/moveJointRelative_{0}', f'psd/pumpSimple_{7}',
                    f'dobot/moveJointRelative_{1}', f'psd/pumpSimple_{8}', f'dobot/moveJointRelative_{2}', f'dobot/moveWaste_{1}', f'psd/pumpSimple_{9}', f'dobot/moveHome_{1}'], 
            params={'start': {'collectionkey' : f'substrate_{substrate}'},
                    f'pumpSimple_{6}': {'volume': -200, 'valve': 7, 'speed': 20, 'times': 1},
                    f'moveJointRelative_{0}':{'x': 0, 'y':0, 'z': 0.5, 'r': 0},
                    f'pumpSimple_{7}': {'volume': -100, 'valve': 7, 'speed': 30, 'times': 1},
                    f'moveJointRelative_{1}':{'x': 0, 'y':0, 'z': 0.5, 'r': 0},
                    f'pumpSimple_{8}': {'volume': -100, 'valve': 7, 'speed': 30, 'times': 1},
                    f'moveJointRelative_{2}':{'x': 0, 'y':0, 'z': 1.0, 'r': 0},
                    f'moveWaste_{1}':{'x': 0, 'y': 0, 'z': 0, 'r': 0},
                    f'pumpSimple_{9}': {'volume': 150, 'speed': 25, 'times': 1},                                    
                    f'moveHome_{1}':{}
                    },
            meta=dict()))

###
test_fnc(dict(soe=['orchestrator/start'], 
                params={'start': {'collectionkey' : f'substrate_{substrate}'}},
                meta=dict()),0)













test_fnc(dict(soe=['orchestrator/start', f'lang/moveWaste_{0}', f'hamilton/pumpL_{0}', f'hamilton/pumpR_{0}', f'lang/moveWaste_{1}', 
                    f'lang/moveWaste_{2}', f'lang/moveWaste_{3}', f'lang/moveWaste_{4}', f'hamilton/pumpL_{1}', f'lang/moveSample_{0}',
                    f'lang/moveDown_{0}', f'lang/getPos_{0}', f'hamilton/pumpL_{2}', f'hamilton/pumpL_{3}', f'hamilton/pumpL_{4}', 
                    f'hamilton/pumpL_{5}', f'hamilton/pumpL_{6}', f'autolab/measure_{0}', f'autolab/measure_{1}', f'autolab/measure_{2}',
                    f'autolab/measure_{3}', f'autolab/measure_{4}', f'autolab/measure_{5}', f'hamilton/pumpL_{7}', f'lang/moveRel_{0}',
                    f'hamilton/pumpL_{8}', f'lang/moveRel_{1}', f'hamilton/pumpL_{9}', f'lang/moveWaste_{5}', f'analysis/eis0_{0}', f'analysis/eis1_{0}'], 
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
                                    'setpointjson': json.dumps({'recordsignal': {'Duration': 30, 'Interval time in µs': 1}}),
                                    'plot': "tCV",
                                    'onoffafter': "off",
                                    'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                    'filename': 'substrate_{}_ocp_{}_{}.nox'.format(substrate, 4, 0),
                                    'parseinstructions':'recordsignal'},
                    f'measure_{1}':{'procedure': 'eis_fast',
                                    'setpointjson': json.dumps({'FHSetSetpointPotential': {'Setpoint value': None}}),
                                    'plot': 'impedance',
                                    'onoffafter': 'off',
                                    'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                    'filename': 'substrate_{}_eis_ocp_{:03d}_{}.nox'.format(substrate, 4, 0),
                                    'parseinstructions': ['FIAMeasPotentiostatic'],
                                    'substrate': substrate,
                                    'id': 0,
                                    'experiment': 0},
                    f'measure_{2}': {'procedure': 'charge',
                                    'setpointjson': json.dumps({'switchgalvanostatic': {'WE(1).Current range': 1+round(math.log10(I0))},
                                                                'applycurrent': {'Setpoint value': -I0},
                                                                'recordsignal': {'Duration': 9000,
                                                                                 'Interval time in µs': 1}}),
                                    'plot': 'tCV',
                                    'onoffafter': 'off',
                                    'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                    'filename': 'substrate_{}_cp_charge_{:03d}_{}.nox'.format(substrate, 4, 1),
                                    'parseinstructions': 'recordsignal'},
                    f'measure_{3}': {'procedure': 'discharge',
                                    'setpointjson': json.dumps({'switchgalvanostatic': {'WE(1).Current range': 1+round(math.log10(I0))},
                                                                'applycurrent': {'Setpoint value': I0},
                                                                'recordsignal': {'Duration': 9000,
                                                                                 'Interval time in µs': 1}}),
                                    'plot': 'tCV',
                                    'onoffafter': 'off',
                                    'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                    'filename': 'substrate_{}_cp_discharge_{:03d}_{}.nox'.format(substrate, 4, 1),
                                    'parseinstructions': 'recordsignal'},
                    f'measure_{4}':{'procedure': 'ocp_rs', 
                                    'setpointjson': json.dumps({'recordsignal': {'Duration': 90, 'Interval time in µs': 1}}),
                                    'plot': "tCV",
                                    'onoffafter': "off",
                                    'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                    'filename': 'substrate_{}_ocp_{}_{}.nox'.format(substrate, 4, 1),
                                    'parseinstructions':'recordsignal'},
                    f'measure_{5}':{'procedure': 'eis_fast',
                                    'setpointjson': json.dumps({'FHSetSetpointPotential': {'Setpoint value': None}}),
                                    'plot': 'impedance',
                                    'onoffafter': 'off',
                                    'safepath': "C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                    'filename': 'substrate_{}_eis_ocp_{:03d}_{}.nox'.format(substrate, 4, 1),
                                    'parseinstructions': ['FIAMeasPotentiostatic'],
                                    'substrate': substrate,
                                    'id': 0,
                                    'experiment': 1},
                    f'pumpL_{7}': {'volume': -75, 'times': 1},
                    f'moveRel_{0}':{'dx': 0, 'dy':0, 'dz':-0.5},
                    f'pumpL_{8}': {'volume': -50, 'times': 1},
                    f'moveRel_{1}':{'dx': 0, 'dy':0, 'dz':-0.5},
                    f'pumpL_{9}': {'volume': -50, 'times': 1},
                    f'moveWaste_{5}':{'x': 0, 'y':0, 'z': 0},
                    f'eis0_{0}': {'run': 0, 'address':json.dumps([f"experiment_{0}:0/measure_{1}/data/data/FIAMeasPotentiostatic/Z'",
                                                            f"experiment_{0}:0/measure_{1}/data/data/FIAMeasPotentiostatic/-Z''",
                                                            f"experiment_{0}:0/measure_{1}/data/data/FIAMeasPotentiostatic/Frequency"])},  
                    f'eis1_{0}': {'run': 1, 'address':json.dumps([f"experiment_{0}:0/measure_{5}/data/data/FIAMeasPotentiostatic/Z'",
                                                        f"experiment_{0}:0/measure_{5}/data/data/FIAMeasPotentiostatic/-Z''",
                                                        f"experiment_{0}:0/measure_{5}/data/data/FIAMeasPotentiostatic/Frequency"])}},
            meta=dict()))

n=1
for i in range(1):
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
                                        'setpointjson': json.dumps({'recordsignal': {'Duration': 60, 'Interval time in µs': 1}}),
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
                                            'setpointjson': json.dumps({'recordsignal': {'Duration': 180, 'Interval time in µs': 1}}),
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
                                            'setpointjson': json.dumps({'recordsignal': {'Duration': 180, 'Interval time in µs': 1}}),
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
                                            'setpointjson': json.dumps({'recordsignal': {'Duration': 180, 'Interval time in µs': 1}}),
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
                    f'eis0_{(i+1)}': {'address':json.dumps([f"experiment_{i+1}:0/measure_{14*(i+1)+1}/data/data/FIAMeasPotentiostatic/Z'",
                                                                f"experiment_{i+1}:0/measure_{14*(i+1)+1}/data/data/FIAMeasPotentiostatic/-Z''",
                                                                f"experiment_{i+1}:0/measure_{14*(i+1)+1}/data/data/FIAMeasPotentiostatic/Frequency"])},  
                    f'eis1_{3*(i+1)}': {'address':json.dumps([f"experiment_{i+1}:0/measure_{14*(i+1)+5}/data/data/FIAMeasPotentiostatic/Z'",
                                                                f"experiment_{i+1}:0/measure_{14*(i+1)+5}/data/data/FIAMeasPotentiostatic/-Z''",
                                                                f"experiment_{i+1}:0/measure_{14*(i+1)+5}/data/data/FIAMeasPotentiostatic/Frequency"])},
                    f'eis1_{3*(i+1)+1}': {'address':json.dumps([f"experiment_{i+1}:0/measure_{14*(i+1)+9}/data/data/FIAMeasPotentiostatic/Z'",
                                                                f"experiment_{i+1}:0/measure_{14*(i+1)+9}/data/data/FIAMeasPotentiostatic/-Z''",
                                                                f"experiment_{i+1}:0/measure_{14*(i+1)+9}/data/data/FIAMeasPotentiostatic/Frequency"])},
                    f'eis1_{3*(i+1)+2}': {'address':json.dumps([f"experiment_{i+1}:0/measure_{14*(i+1)+13}/data/data/FIAMeasPotentiostatic/Z'",
                                                                f"experiment_{i+1}:0/measure_{14*(i+1)+13}/data/data/FIAMeasPotentiostatic/-Z''",
                                                                f"experiment_{i+1}:0/measure_{14*(i+1)+13}/data/data/FIAMeasPotentiostatic/Frequency"])},                                                                                        
                    f'activeLearningGaussian_{i+1}': {'name': 'sdc_4', 'num': int(i+1), 'query': query, 'address':f'experiment_{i+1}:0/cp_{i+1}/data'}}, 
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