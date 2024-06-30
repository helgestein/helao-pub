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



V = 500
substrate = 1033

def generate_spot_positions(initial_x, num_positions, increment):
    return [initial_x + increment*i for i in range(num_positions)]

initial_x = 5
num_positions = 10
increment = 5
x_positions = generate_spot_positions(initial_x, num_positions, increment)

initial_measurement = ("NiHCF", {'V1': 0, 'V2': 0, 'V3': V/2, 'V4': V/2, 'V5': 0})

measurement_methods = [
    #{
    #    'method': 'cyclic_voltammetry',
    #    'parameters': json.dumps({
    #        "equilibration_time": 5,  
    #        "e_begin": 0.5,          
    #        "e_vtx1": 0.9,           
    #        "e_vtx2": 0,             
    #        "e_step": 0.05,          
    #        "scan_rate": 0.05,        
    #        "n_scans": 3           
    #    }),
    #    'suffix': 'cv'
    #},
    {
        'method': 'chronoamperometry',
        'parameters': json.dumps({
                'e_deposition': 0.64,      # DepositionPotential
                't_deposition': 40.0,      #DepositionTime
                'e_conditioning': 0.0,    # ConditioningPotential: A fixed potential is applied to the cell for a defined period of time before the experiment starts.
                't_conditioning': 0.0,    # ConditioningTime
                'equilibration_time': 0.0, # EquilibrationTime
                'interval_time': 0.1,     # IntervalTime
                'e_applied': 0.0,         # AppliedPotential
                'run_time': 1.0           # RunTime
            }),
            'suffix': 'chronoamp'
    }
    #{   'method': 'linear_sweep_potentiometry',
    #    'parameters': json.dumps({
    #            'e_deposition': 0.0,      # DepositionPotential
    #            't_deposition': 0.0,      #DepositionTime
    #            'e_conditioning': 0.0,    # ConditioningPotential
    #            't_conditioning': 0.0,    # ConditioningTime
    #            'i_begin': -1.0,          # BeginCurrent
    #            'i_end': 1.0,             # EndCurrent
    #            'i_step': 0.01,          #StepCurrent
    #            'scan_rate': 1.0,         # ScanrateG **not a typo**
    #            't_run': 5.0,
    #            'e_max': 0.5,
    #            'e_max_bool': False,
    #            'e_min': -0.5,
    #            'e_min_bool': False
    #        }),
    #        'suffix': 'lin_sweep_pot'
    #},
    #{
    #    'method': 'linear_sweep_voltammetry',
    #    'parameters': json.dumps({
    #            'e_deposition': 0.0,      # DepositionPotential
    #            't_deposition': 0.0,      #DepositionTime
    #            'e_conditioning': 0.0,    # ConditioningPotential
    #            't_conditioning': 0.0,    # ConditioningTime
    #            'equilibration_time': 2.0, # EquilibrationTime
    #            'e_begin': -1.0,          # BeginPotential
    #            'e_end': 1.0,             # EndPotential
    #            'i_step': 0.01,          #StepPotential
    #            'scan_rate': 1.0         # ScanrateG **not a typo**
    #        }),
    #        'suffix': 'lin_sweep_volt'
    #},
    #{
    #    'method': 'chronopotentiometry',
    #    'parameters': json.dumps({
    #            'e_deposition': 0.0,     # DepositionPotential
    #            't_deposition': 0.0,     # DepositionTime
    #            'e_conditioning': 0.0,   # ConditioningPotential
    #            't_conditioning': 0.0,   # ConditioningTime
    #            'i': 1e-6,               # Current in Amps
    #            't_interval': 0.2,       # IntervalTime
    #            't_run': 5.0,            # RunTime
    #            'e_max': 0.5,            # LimitMaxValue, should be 10 times smaller than actual value
    #            'e_max_bool': False,     # UseMaxValue
    #            'e_min': -0.5,           # LimitMinValue, should be 10 times smaller than actual value
    #            'e_min_bool': False      # UseMinValue
    #        }),
    #        'suffix': 'chronopot'
    #},
    #{
    #    'method': 'square_wave_voltammetry',
    #    'parameters': json.dumps({
    #            'e_deposition': 0.0,     # DepositionPotential
    #            't_deposition': 0.0,     # DepositionTime
    #            'e_conditioning': 0.0,   # ConditioningPotential
    #            't_conditioning': 0.0,   # ConditioningTime
    #            'equilibration_time': 0, # EquilibrationTime
    #            'e_begin': -0.25,        # BeginPotential
    #            'e_end': 0.5,            # EndPotential
    #            'e_step': 0.01,          # StepPotential
    #            'amplitude': 0.1,        # PulseAmplitude
    #            'frequency': 20,          # Frequency
    #            'i': 1e-6,               # Current in Amps
    #            't_interval': 0.2,       # IntervalTime
    #            't_run': 5.0,            # RunTime
    #            'e_max': 0.5,            # LimitMaxValue, should be 10 times smaller than actual value
    #            'e_max_bool': False,     # UseMaxValue
    #            'e_min': -0.5,           # LimitMinValue, should be 10 times smaller than actual value
    #            'e_min_bool': False      # UseMinValue
    #    }),
    #        'suffix': 'sq_wave_volt'
    #}
]

def perform_test_run(run_index, x, measure_name, measurement_method):
    while True:
        spot_number = f"{x}10"
        steps = [
            f'orchestrator/start', 
            f'dobot/moveHome_{run_index}', 
            f'dobot/moveWaste_{run_index}',
            f'pumpVial_{run_index}', 
            f'dobot/removeDrop_{run_index}', 
            f'dobot/removeDrop_{run_index+1}',
            f'dobot/moveSample_{run_index}', 
            f'dobot/moveSample_{run_index+1}', 
            f'dobot/moveDown_{run_index}', 
            f'palmsens/check_ocp_{run_index}',
            f'palmsens/measure_{run_index}',
            f'palmsens/measure_{run_index+2}',
            f'dobot/moveHome_{run_index+1}'
        ]
        
        params = {
            'start': {'collectionkey': f'substrate_{substrate}'},
            f'moveHome_{run_index}': {},
            f'moveWaste_{run_index}': {'x': 0, 'y': 0, 'z': 0, 'r': 0},
            f'pumpVial_{run_index}': {'volume': 350, 'speed': 15, 'times': 1},
            f'removeDrop_{run_index}': {'x': 0, 'y': 3.5, 'z': 0, 'r': 0},
            f'removeDrop_{run_index+1}': {'x': 0, 'y': 3.5, 'z': 0, 'r': 0}, 
            f'moveSample_{run_index}': {'x': x, 'y': 10, 'z': 0, 'r': 0},
            f'moveSample_{run_index+1}': {'x': x, 'y': 10, 'z': -13.8, 'r': 0},
            f'moveDown_{run_index}': {'dz': 0.05, 'steps': 50, 'maxForce': 200, 'threshold': 0.1},
            f'check_ocp_{run_index}': {
                'method': 'open_circuit_potentiometry',
                'parameters': json.dumps({'t_run': 30, 't_interval': 0.25}),
                'filename': f'substrate_{substrate}_{measure_name}_check_ocp_{spot_number}',
                'substrate': substrate,
                'id': spot_number,
                'experiment': 0
            },
            f'measure_{run_index}': {
                'method': 'potentiostatic_impedance_spectroscopy',
                'parameters': json.dumps({
                    "e_dc": 0.0,                 
                    "e_ac": 0.01,                
                    "n_frequencies": 41,         
                    "max_frequency": 1e5,        
                    "min_frequency": 1e1,        
                    "meas_vs_ocp_true": 1,       
                    "t_max_ocp": 20.0,           
                    "stability_criterion": 0.001 
                }),
                'filename': f'substrate_{substrate}_{measure_name}_peis_{spot_number}_{j}',
                'substrate': substrate,
                'id': spot_number,
                'experiment': 0
            },
            f'measure_{run_index+2}': {
                'method': measurement_method['method'],
                'parameters': measurement_method['parameters'],
                'filename': f'substrate_{substrate}_{measure_name}_{measurement_method["suffix"]}_{spot_number}',
                'substrate': substrate,
                'id': spot_number,
                'experiment': 0
            },
            f'moveHome_{run_index+1}': {}       
        }

        def get_ocp_value(filename):
            with open(filename, 'r') as file:
                data = json.load(file)
                ocp_values = data['potential']
                average_ocp = sum(ocp_values) / len(ocp_values)
                return average_ocp

        ocp_value = get_ocp_value(f'substrate_{substrate}_{measure_name}_ocp_{spot_number}')
        if ocp_value > 0.7 or ocp_value < 0.4:
            perform_test_run(run_index, x, measure_name, measurement_method)

for i, measurement_method in enumerate(measurement_methods):
    x = x_positions[i]
    perform_test_run(i, x, initial_measurement[0], measurement_method)





# Define volumes
V = 1000
substrate = 1033

# Define a function to generate spot positions
def generate_spot_positions():
    return [0 + 2*i for i in range(1)]  # Generate 21 positions, incrementing x by 2 each time

# Generate spot positions
x_positions = generate_spot_positions()

# Define measurements
measurements = [
    ("NiHCF", {'V1': 0, 'V2': 0, 'V3': V/2, 'V4': V/2, 'V5': 0}),
    #("Ni0.8Mn0.2HCF", {'V1': 0, 'V2': 0, 'V3':0.8*V/2, 'V4': V/2, 'V5': 0.2*V/2}),
    #("Ni0.6Mn0.4HCF", {'V1': 0, 'V2': 0, 'V3': 0.6*V/2, 'V4': V/2, 'V5': 0.4*V/2}),
    #("Ni0.4Mn0.6HCF", {'V1': 0, 'V2': 0, 'V3': 0.4*V/2, 'V4': V/2, 'V5': 0.6*V/2}),
    #("Ni0.2Mn0.8HCF", {'V1': 0, 'V2': 0, 'V3': 0.2*V/2, 'V4': V/2, 'V5': 0.8*V/2}),
    #("MnHCF", {'V1': 0, 'V2': 0, 'V3': 0, 'V4': V/2, 'V5': V/2})
]

# Iterate over each measurement type and generate 3 measurements for each
for measure_index, (measure_name, pump_mix_volumes) in enumerate(measurements):
    for j in range(1):
        x = x_positions[measure_index * 3 + j]
        spot_number = f"{x}40"  # Dynamically create spot number
        test_fnc(dict(soe=[
            f'orchestrator/start', 
            f'dobot/moveHome_{measure_index}', 
            f'dobot/moveWaste_{measure_index}', 
            f'psd/pumpMix_{measure_index}', 
            f'psd/pumpVial_{measure_index}', 
            f'dobot/removeDrop_{measure_index}', 
            f'dobot/removeDrop_{measure_index+1}',
            f'dobot/moveSample_{measure_index}', 
            f'dobot/moveSample_{measure_index+1}', 
            #f'psd/pumpSimple_{measure_index}', 
            f'dobot/moveDown_{measure_index}', 
            #f'psd/pumpVial_{measure_index+1}', 
            #f'psd/pumpSimple_{measure_index+1}', 
            #f'psd/pumpVial_{measure_index+2}',
            f'palmsens/measure_{measure_index}', 
            f'palmsens/measure_{measure_index+1}', 
            f'palmsens/measure_{measure_index+2}',
            f'palmsens/measure_{measure_index+2}',
            f'palmsens/measure_{measure_index+2}',
            f'palmsens/measure_{measure_index+2}',
            #f'psd/pumpSimple_{measure_index+2}',
            f'dobot/moveJointRelative_{measure_index}', 
            f'dobot/moveWaste_{measure_index+1}', 
            f'psd/pumpVial_{measure_index+1}', 
            f'psd/pumpMix_{measure_index+1}', 
            f'dobot/moveHome_{measure_index+1}'
        ],
        params={
            'start': {'collectionkey': f'substrate_{substrate}'},
            f'moveHome_{measure_index}': {},
            f'moveWaste_{measure_index}': {'x': 0, 'y': 0, 'z': 0, 'r': 0},
            f'pumpMix_{measure_index}': {**pump_mix_volumes, 'V6': 0, 'speed': 20, 'mix': 1, 'times': 1, 'cell': False},
            f'pumpVial_{measure_index}': {'volume': 350, 'speed': 15, 'times': 1},
            f'removeDrop_{measure_index}': {'x': 0, 'y': 3.5, 'z': 0, 'r': 0},
            f'removeDrop_{measure_index+1}': {'x': 0, 'y': 3.5, 'z': 0, 'r': 0}, 
            f'moveSample_{measure_index}': {'x': x, 'y': 40, 'z': 0, 'r': 0},
            f'moveSample_{measure_index+1}': {'x': x, 'y': 40, 'z': -13.8, 'r': 0},
            #f'pumpSimple_{measure_index}': {'volume': -15, 'valve': 7, 'speed': 30, 'times': 1},
            f'moveDown_{measure_index}': {'dz': 0.05, 'steps': 50, 'maxForce': 200, 'threshold': 0.1},
            #f'pumpVial_{measure_index+1}': {'volume': 15, 'speed': 30, 'times': 1},
            #f'pumpSimple_{measure_index+1}': {'volume': -15, 'valve': 7, 'speed': 30, 'times': 1},
            #f'pumpVial_{measure_index+2}': {'volume': 15, 'speed': 30, 'times': 1},
            f'measure_{measure_index}': {
                'method': 'open_circuit_potentiometry',
                'parameters': json.dumps({'t_run': 30, 't_interval': 0.25}),
                'filename': f'substrate_{substrate}_{measure_name}_ocp_{spot_number}_{j}',
                'substrate': substrate,
                'id': spot_number,
                'experiment': 0
            },
            f'measure_{measure_index+1}': {
                'method': 'potentiostatic_impedance_spectroscopy',
                'parameters': json.dumps({
                    "e_dc": 0.0,                 
                    "e_ac": 0.01,                
                    "n_frequencies": 41,         
                    "max_frequency": 1e5,        
                    "min_frequency": 1e1,        
                    "meas_vs_ocp_true": 1,       
                    "t_max_ocp": 20.0,           
                    "stability_criterion": 0.001 
                }),
                'filename': f'substrate_{substrate}_{measure_name}_peis_{spot_number}_{j}',
                'substrate': substrate,
                'id': spot_number,
                'experiment': 0
            },
            f'measure_{measure_index+2}': {
                'method': 'cyclic_voltammetry',
                'parameters': json.dumps({
                    "equilibration_time": 5,  
                    "e_begin": 0.5,          
                    "e_vtx1": 0.9,           
                    "e_vtx2": 0,             
                    "e_step": 0.05,          
                    "scan_rate": 0.05,        
                    "n_scans": 3           
                }),
                'filename': f'substrate_{substrate}_{measure_name}_cv_{spot_number}_{j}',
                'substrate': substrate,
                'id': spot_number,
                'experiment': 0
            },
            f'measure_{measure_index+2}': {
                'method': 'chronoamperometry',
                'parameters': json.dumps({
                            'e_deposition': 0.0,      # DepositionPotential
                            't_deposition': 0.0,      #DepositionTime
                            'e_conditioning': 0.0,    # ConditioningPotential
                            't_conditioning': 0.0,    # ConditioningTime
                            'equilibration_time': 0.0, # EquilibrationTime
                            'interval_time': 0.1,     # IntervalTime
                            'e_applied': 0.0,         # AppliedPotential
                            'run_time': 1.0           # RunTime
                }),
                'filename': f'substrate_{substrate}_{measure_name}_chronoamperometry_{spot_number}_{j}',
                'substrate': substrate,
                'id': spot_number,
                'experiment': 0
            },
            f'measure_{measure_index+2}': {
                'method': 'linear_sweep_potentiometry',
                'parameters': json.dumps({
                            'e_deposition': 0.0,      # DepositionPotential
                            't_deposition': 0.0,      #DepositionTime
                            'e_conditioning': 0.0,    # ConditioningPotential
                            't_conditioning': 0.0,    # ConditioningTime
                            'i_begin': -1.0,          # BeginCurrent
                            'i_end': 1.0,             # EndCurrent
                            'i_step': 0.01,          #StepCurrent
                            'scan_rate': 1.0,         # ScanrateG **not a typo**
                            't_run': 5.0,
                            'e_max': 0.5,
                            'e_max_bool': False,
                            'e_min': -0.5,
                            'e_min_bool': False
                }),
                'filename': f'substrate_{substrate}_{measure_name}_linear_sweep_potentiometry_{spot_number}_{j}',
                'substrate': substrate,
                'id': spot_number,
                'experiment': 0
            },
            f'measure_{measure_index+2}': {
                'method': 'linear_sweep_voltammetry',
                'parameters': json.dumps({
                            'e_deposition': 0.0,      # DepositionPotential
                            't_deposition': 0.0,      #DepositionTime
                            'e_conditioning': 0.0,    # ConditioningPotential
                            't_conditioning': 0.0,    # ConditioningTime
                            'equilibration_time': 2.0, # EquilibrationTime
                            'e_begin': -1.0,          # BeginPotential
                            'e_end': 1.0,             # EndPotential
                            'i_step': 0.01,          #StepPotential
                            'scan_rate': 1.0,         # ScanrateG **not a typo**
                }),
                'filename': f'substrate_{substrate}_{measure_name}_linear_sweep_voltammetry_{spot_number}_{j}',
                'substrate': substrate,
                'id': spot_number,
                'experiment': 0
            },
            f'measure_{measure_index+2}': {
                'method': 'chronopotentiometry',
                'parameters': json.dumps({
                            'e_deposition': 0.0,     # DepositionPotential
                            't_deposition': 0.0,     # DepositionTime
                            'e_conditioning': 0.0,   # ConditioningPotential
                            't_conditioning': 0.0,   # ConditioningTime
                            'i': 1e-6,               # Current in Amps
                            't_interval': 0.2,       # IntervalTime
                            't_run': 5.0,            # RunTime
                            'e_max': 0.5,            # LimitMaxValue, should be 10 times smaller than actual value
                            'e_max_bool': False,     # UseMaxValue
                            'e_min': -0.5,           # LimitMinValue, should be 10 times smaller than actual value
                            'e_min_bool': False      # UseMinValue
                }),
                'filename': f'substrate_{substrate}_{measure_name}_chronopotentiometry_{spot_number}_{j}',
                'substrate': substrate,
                'id': spot_number,
                'experiment': 0
            },
            f'measure_{measure_index+2}': {
                'method': 'square_wave_voltammetry',
                'parameters': json.dumps({
                            'e_deposition': 0.0,     # DepositionPotential
                            't_deposition': 0.0,     # DepositionTime
                            'e_conditioning': 0.0,   # ConditioningPotential
                            't_conditioning': 0.0,   # ConditioningTime
                            'equilibration_time': 0, # EquilibrationTime
                            'e_begin': -0.25,        # BeginPotential
                            'e_end': 0.5,            # EndPotential
                            'e_step': 0.01,          # StepPotential
                            'amplitude': 0.1,        # PulseAmplitude
                            'frequency': 20          # Frequency
                            'i': 1e-6,               # Current in Amps
                            't_interval': 0.2,       # IntervalTime
                            't_run': 5.0,            # RunTime
                            'e_max': 0.5,            # LimitMaxValue, should be 10 times smaller than actual value
                            'e_max_bool': False,     # UseMaxValue
                            'e_min': -0.5,           # LimitMinValue, should be 10 times smaller than actual value
                            'e_min_bool': False      # UseMinValue
                }),
                'filename': f'substrate_{substrate}_{measure_name}square_wave_voltammetry_{spot_number}_{j}',
                'substrate': substrate,
                'id': spot_number,
                'experiment': 0
            },
            #f'pumpSimple_{measure_index+2}': {'volume': -100, 'valve': 7, 'speed': 25, 'times': 1},
            f'moveJointRelative_{measure_index}': {'x': 0, 'y': 0, 'z': 2, 'r': 0},
            f'moveWaste_{measure_index+1}': {},
            f'pumpVial_{measure_index+1}': {'volume': 600, 'speed': 15, 'times': 1},
            f'pumpMix_{measure_index+1}': {'V1': 0, 'V2': 350, 'V3': 0, 'V4': 0, 'V5': 0, 'V6': 0, 'speed': 15, 'mix': 3, 'times': 2, 'cell': True},
            f'moveHome_{measure_index+1}': {}
        },
        meta=dict()))

test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))


substrate = 1034

test_fnc(dict(soe=['orchestrator/start', f'dobot/moveHome_{0}', f'dobot/moveWaste_{0}', f'psd/pumpSimple_{0}', f'dobot/removeDrop_{0}', f'dobot/removeDrop_{1}', f'dobot/moveSample_{0}', f'dobot/moveSample_{1}',
                   f'dobot/moveDown_{0}', f'psd/pumpSimple_{1}',f'psd/pumpSimple_{2}',f'psd/pumpSimple_{3}',
                   f'palmsens/measure_{0}', f'palmsens/measure_{1}', #f'palmsens/measure_{2}',
                   f'palmsens/measure_{2}', f'psd/pumpSimple_{4}',
                   #f'psd/pumpSimple_{3}',f'palmsens/measure_{4}',
                   f'dobot/moveJointRelative_{0}', f'dobot/moveWaste_{1}', f'psd/pumpSimple_{5}', f'dobot/moveHome_{1}'], 
            params={'start': {'collectionkey' : f'substrate_{substrate}'},
                    f'moveHome_{0}':{},
                    f'moveWaste_{0}':{'x': 0, 'y':0, 'z': 0, 'r': 0},
                    f'pumpSimple_{0}':{'volume': 350, 'valve': 5, 'speed': 25, 'times': 1},
                    f'removeDrop_{0}' : {'x': 0, 'y': 3.5, 'z': 0, 'r': 0},
                    f'removeDrop_{1}' : {'x': 0, 'y': 3.5, 'z': 0, 'r': 0},
                    f'moveSample_{0}':{'x': 25, 'y':20, 'z': 0, 'r': 0},
                    f'moveSample_{1}':{'x': 25, 'y':20, 'z': -13.6, 'r': 0},
                    f'moveDown_{0}': {'dz': 0.05, 'steps': 50, 'maxForce': 50, 'threshold': 0.1},
                    f'pumpSimple_{1}':{'volume': 20, 'valve': 5, 'speed': 25, 'times': 1},
                    f'pumpSimple_{2}':{'volume': -10, 'valve': 7, 'speed': 25, 'times': 1},
                    f'pumpSimple_{3}':{'volume': 20, 'valve': 5, 'speed': 25, 'times': 1},
                    f'measure_{0}':{'method': 'open_circuit_potentiometry',
                                    'parameters': json.dumps({'t_run': 30, 't_interval': 0.25}),
                                    'filename': 'substrate_{}_dummy_ocp_{}_{}'.format(substrate, 0, 0),
                                    'substrate': substrate,
                                    'id': 0,
                                    'experiment': 0},
                    f'measure_{1}':{'method': 'potentiostatic_impedance_spectroscopy',
                                    'parameters': json.dumps({
                                        "e_dc": 0.0,                 # DC potential
                                        "e_ac": 0.01,                # AC potential (10 mV/s)
                                        "n_frequencies": 41,         # Number of frequencies
                                        "max_frequency": 1e5,        # Maximum frequency
                                        "min_frequency": 1e1,        # Minimum frequency
                                        "meas_vs_ocp_true": 1,       # Measure vs OCP
                                        "t_max_ocp": 20.0,           # Maximum time OCP stabilization
                                        "stability_criterion": 0.001 # Stability criterion in mV/s
                                        }),
                                    'filename': 'substrate_{}_dummy_peis_{}_{}'.format(substrate, 0, 0),
                                    'substrate': substrate,
                                    'id': 0,
                                    'experiment': 0},
                    #f'measure_{2}':{'method': 'galvanostatic_impedance_spectroscopy',
                                    #'parameters': json.dumps({
                                        #"i_input_range": -4,       # DC current range
                                        #"i_dc": 0.1,               # DC current * range
                                        #"i_ac": 0.01,              # AC current * range
                                        #"n_frequencies": 31,       # Number of frequencies
                                        #"max_frequency": 5e4,      # Maximum frequency
                                        #"min_frequency": 5e1       # Minimum frequency
                                        #}),
                                    #'filename': 'substrate_{}_dummy_geis_potentiost_{}_{}'.format(substrate, 0, 0),
                                    #'substrate': substrate,
                                    #'id': 0,
                                    #'experiment': 0},
                    f'measure_{2}':{'method': 'cyclic_voltammetry',
                                    'parameters': json.dumps({"equilibration_time": 5,  # Equilibration time in seconds
                                        "e_begin": 0.5,          # Begin potential in volts
                                        "e_vtx1": 0,           # Vertex 1 potential in volts
                                        "e_vtx2": 0.9,            # Vertex 2 potential in volts
                                        "e_step": 0.01,           # Step potential in volts
                                        "scan_rate": 0.2,         # Scan rate in V/s
                                        "n_scans": 10              # Number of scans
                                        }),
                                    'filename': 'substrate_{}_dummy_cv_{}_{}'.format(substrate, 0, 0),
                                    'substrate': substrate,
                                    'id': 0,
                                    'experiment': 0},
                    f'pumpSimple_{4}':{'volume': -100, 'valve': 7, 'speed': 25, 'times': 1},
                    f'moveJointRelative_{0}':{'x': 0, 'y':0, 'z': 2, 'r': 0},
                    f'moveWaste_{1}':{'x': 0, 'y':0, 'z': 0, 'r': 0},
                    f'pumpSimple_{5}':{'volume': 100, 'valve': 2, 'speed': 20, 'times': 1},
                    f'moveHome_{1}':{}
                    },
            meta=dict()))

test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))

Mn = 0.5
HCF = 0.5
V = 1000
spot_number = 1030
substrate = 1020

# Define a function to generate spot positions
def generate_spot_positions():
    x_positions = [10 + i * 5 for i in range(4)]  # Generate 4 positions
    return x_positions

# Generate spot positions
x_positions = generate_spot_positions()

for i in range(4):
    x = x_positions[i]
    test_fnc(dict(soe=['orchestrator/start', f'dobot/moveHome_{i}', f'dobot/moveWaste_{i}', f'psd/pumpMix_{i}', f'psd/pumpVial_{i}', f'dobot/removeDrop_{i}', f'dobot/removeDrop_{i+1}',
                       f'psd/pumpSimple_{i}', f'dobot/moveSample_{i}', f'dobot/moveSample_{i+1}', f'dobot/moveDown_{i}', f'psd/pumpVial_{i+1}', f'psd/pumpSimple_{i+1}', f'psd/pumpVial_{i+2}',
                       f'palmsens/measure_{i}', f'palmsens/measure_{i+1}', f'palmsens/measure_{i+2}', f'psd/pumpSimple_{i+2}',
                       f'dobot/moveJointRelative_{i}', f'dobot/moveWaste_{i+1}', f'psd/pumpVial_{i+3}', f'psd/pumpMix_{i+1}', f'dobot/moveHome_{i+1}'],
                params={'start': {'collectionkey': f'substrate_{substrate}'},
                        f'moveHome_{i}': {},
                        f'moveWaste_{i}': {'x': 0, 'y': 0, 'z': 0, 'r': 0},
                        f'pumpMix_{i}': {'V1': 0, 'V2': 0, 'V3': 0, 'V4': V*HCF, 'V5': V*Mn, 'V6': 0, 'speed': 30, 'mix': 3, 'times': 1, 'cell': False},
                        f'pumpVial_{i}': {'volume': 350, 'speed': 15, 'times': 1},
                        f'removeDrop_{i}': {'x': 0, 'y': 3.5, 'z': 0, 'r': 0},
                        f'removeDrop_{i+1}': {'x': 0, 'y': 3.5, 'z': 0, 'r': 0},
                        f'pumpSimple_{i}': {'volume': -15, 'valve': 7, 'speed': 30, 'times': 1},
                        f'moveSample_{i}': {'x': x, 'y': 30, 'z': 0, 'r': 0},
                        f'moveSample_{i+1}': {'x': x, 'y': 30, 'z': -13.8, 'r': 0},
                        f'moveDown_{i}': {'dz': 0.05, 'steps': 50, 'maxForce': 150, 'threshold': 0.1},
                        f'pumpVial_{i+1}': {'volume': 35, 'speed': 30, 'times': 1},
                        f'pumpSimple_{i+1}': {'volume': -15, 'valve': 7, 'speed': 30, 'times': 1},
                        f'pumpVial_{i+2}': {'volume': 30, 'speed': 30, 'times': 1},
                        f'measure_{i}': {'method': 'open_circuit_potentiometry',
                                        'parameters': json.dumps({'t_run': 30, 't_interval': 0.25}),
                                        'filename': 'substrate_{}_dummy_ocp_{}_{}'.format(substrate, spot_number, i),
                                        'substrate': substrate,
                                        'id': spot_number,
                                        'experiment': i},
                        f'measure_{i+1}': {'method': 'potentiostatic_impedance_spectroscopy',
                                           'parameters': json.dumps({
                                               "e_dc": 0.0,                 # DC potential
                                               "e_ac": 0.01,                # AC potential (10 mV/s)
                                               "n_frequencies": 41,         # Number of frequencies
                                               "max_frequency": 1e5,        # Maximum frequency
                                               "min_frequency": 1e1,        # Minimum frequency
                                               "meas_vs_ocp_true": 1,       # Measure vs OCP
                                               "t_max_ocp": 20.0,           # Maximum time OCP stabilization
                                               "stability_criterion": 0.001 # Stability criterion in mV/s
                                           }),
                                           'filename': 'substrate_{}_dummy_peis_{}_{}'.format(substrate, spot_number, i+1),
                                           'substrate': substrate,
                                           'id': spot_number,
                                           'experiment': i+1},
                        f'measure_{i+2}': {'method': 'cyclic_voltammetry',
                                           'parameters': json.dumps({"equilibration_time": 5,  # Equilibration time in seconds
                                                                     "e_begin": 0.5,          # Begin potential in volts
                                                                     "e_vtx1": 0.9,           # Vertex 1 potential in volts
                                                                     "e_vtx2": 0,             # Vertex 2 potential in volts
                                                                     "e_step": 0.05,          # Step potential in volts
                                                                     "scan_rate": 0.1,        # Scan rate in V/s
                                                                     "n_scans": 100           # Number of scans
                                           }),
                                           'filename': 'substrate_{}_dummy_cv_{}_{}'.format(substrate, spot_number, i+2),
                                           'substrate': substrate,
                                           'id': spot_number,
                                           'experiment': i+2},
                        f'pumpSimple_{i+2}': {'volume': -100, 'valve': 7, 'speed': 25, 'times': 1},
                        f'moveJointRelative_{i}': {'x': 0, 'y': 0, 'z': 2, 'r': 0},
                        f'moveWaste_{i+1}': {},
                        f'pumpVial_{i+3}': {'volume': 800, 'speed': 15, 'times': 1},
                        f'pumpMix_{i+1}': {'V1': 0, 'V2': 350, 'V3': 0, 'V4': 0, 'V5': 0, 'V6': 0, 'speed': 15, 'mix': 3, 'times': 2, 'cell': True},
                        f'moveHome_{i+1}': {}
                        },
                meta=dict()))

test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))







# Define the scan rates
scan_rates = [0.002, 0.005, 0.01, 0.02, 0.05, 0.2]  # Scan rates in V/s (2, 5, 10, 20, 50, 200 mV/s)

substrate = 1013

for i, scan_rate in enumerate(scan_rates):
    # Update the x-coordinate for each run
    x_coordinate = 15 + i * 5

    # Update the parameters for cyclic_voltammetry and the sample position
    params = {
        'start': {'collectionkey' : f'substrate_{substrate}'},
        f'moveHome_{0}':{},
        f'moveWaste_{0}':{'x': 0, 'y':0, 'z': 0, 'r': 0},
        f'pumpMix_{0}':{'V1':0, 'V2':315, 'V3':0, 'V4':35, 'V5':0, 'V6':0, 'speed':10, 'mix':1, 'times':1, 'cell':True},
        f'removeDrop_{0}' : {'x': 0, 'y': 0, 'z': 0, 'r': 0},
        f'removeDrop_{1}' : {'x': 0, 'y': 0, 'z': 0, 'r': 0},
        f'moveSample_{0}':{'x': x_coordinate, 'y': 25, 'z': 0, 'r': 0},
        f'moveSample_{1}':{'x': x_coordinate, 'y': 25, 'z': -13.6, 'r': 0},
        f'moveDown_{0}': {'dz': 0.05, 'steps': 50, 'maxForce': 50, 'threshold': 0.1},
        f'pumpMix_{1}':{'V1':0, 'V2':18, 'V3':0, 'V4':2, 'V5':0, 'V6':0, 'speed':10, 'mix':1, 'times':1, 'cell':True},
        f'pumpSimple_{0}':{'volume': -10, 'valve': 7, 'speed': 25, 'times': 1},
        f'pumpMix_{2}':{'V1':0, 'V2':18, 'V3':0, 'V4':2, 'V5':0, 'V6':0, 'speed':10, 'mix':1, 'times':1, 'cell':True},
        f'measure_{0}':{'method': 'open_circuit_potentiometry',
                        'parameters': json.dumps({'t_run': 30, 't_interval': 0.25}),
                        'filename': 'substrate_{}_dummy_ocp_{}_{}'.format(substrate, 0, i),
                        'substrate': substrate,
                        'id': i,
                        'experiment': i},
        f'measure_{1}':{'method': 'potentiostatic_impedance_spectroscopy',
                        'parameters': json.dumps({
                            "e_dc": 0.0,                 # DC potential
                            "e_ac": 0.01,                # AC potential (10 mV/s)
                            "n_frequencies": 41,         # Number of frequencies
                            "max_frequency": 1e5,        # Maximum frequency
                            "min_frequency": 1e1,        # Minimum frequency
                            "meas_vs_ocp_true": 1,       # Measure vs OCP
                            "t_max_ocp": 20.0,           # Maximum time OCP stabilization
                            "stability_criterion": 0.001 # Stability criterion in mV/s
                            }),
                        'filename': 'substrate_{}_dummy_peis_{}_{}'.format(substrate, 0, i),
                        'substrate': substrate,
                        'id': i,
                        'experiment': i},
        f'measure_{2}':{'method': 'cyclic_voltammetry',
                        'parameters': json.dumps({"equilibration_time": 5,  # Equilibration time in seconds
                            "e_begin": 0.0,          # Begin potential in volts
                            "e_vtx1": -0.3,           # Vertex 1 potential in volts
                            "e_vtx2": 0.8,            # Vertex 2 potential in volts
                            "e_step": 0.01,           # Step potential in volts
                            "scan_rate": scan_rate,   # Scan rate in V/s
                            "n_scans": 10             # Number of scans
                            }),
                        'filename': 'substrate_{}_dummy_cv_{}_{}'.format(substrate, 0, i),
                        'substrate': substrate,
                        'id': i,
                        'experiment': i},
        f'pumpSimple_{1}':{'volume': -100, 'valve': 7, 'speed': 25, 'times': 1},
        f'moveJointRelative_{0}':{'x': 0, 'y':0, 'z': 2, 'r': 0},
        f'moveWaste_{1}':{},
        f'pumpSimple_{2}':{'volume': 20, 'valve': 2, 'speed': 25, 'times': 1},
        f'moveHome_{1}':{}
    }

    test_fnc(dict(soe=[
        'orchestrator/start', f'dobot/moveHome_{0}', f'dobot/moveWaste_{0}', f'psd/pumpMix_{0}', f'dobot/removeDrop_{0}', f'dobot/removeDrop_{1}', f'dobot/moveSample_{0}', f'dobot/moveSample_{1}',
        f'dobot/moveDown_{0}', f'psd/pumpMix_{1}', f'psd/pumpSimple_{0}', f'psd/pumpMix_{2}', f'palmsens/measure_{0}', f'palmsens/measure_{1}', f'palmsens/measure_{2}', f'psd/pumpSimple_{1}',
        f'dobot/moveJointRelative_{0}', f'dobot/moveWaste_{1}', f'psd/pumpSimple_{2}', f'dobot/moveHome_{1}'
    ], params=params, meta=dict()))




substrate=1032
test_fnc(dict(soe=['orchestrator/start', f'palmsens/measure_{0}', f'palmsens/measure_{1}', 
                    f'dobot/moveHome_{0}'], 
            params={'start': {'collectionkey' : f'substrate_{substrate}'},
                    f'measure_{0}':{'method': 'open_circuit_potentiometry',
                                    'parameters': json.dumps({'t_run': 2.5, 't_interval': 0.25}),
                                    'filename': 'substrate_{}_dummy_ocp_{}_{}'.format(substrate, 0, 0),
                                    'substrate': substrate,
                                    'id': 0,
                                    'experiment': 0},
                    f'measure_{1}':{'method': 'cyclic_voltammetry',
                        'parameters': json.dumps({"equilibration_time": 5,  # Equilibration time in seconds
                            "e_begin": 0.6,          # Begin potential in volts
                            "e_vtx1": 0.9,           # Vertex 1 potential in volts
                            "e_vtx2": 0.0,            # Vertex 2 potential in volts
                            "e_step": 0.01,           # Step potential in volts
                            "scan_rate": 0.05,   # Scan rate in V/s
                            "n_scans": 10             # Number of scans
                            }),
                        'filename': 'substrate_{}_dummy_cv_{}_{}'.format(substrate, 0, 0),
                                    'substrate': substrate,
                                    'id': 0,
                                    'experiment': 0},
                    f'moveHome_{0}':{}
                    },
            meta=dict()))

test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))

substrate=1033
test_fnc(dict(soe=['orchestrator/start', f'palmsens/measure_{0}',
                   f'palmsens/measure_{1}', f'palmsens/measure_{2}',
                    f'dobot/moveHome_{0}'], 
            params={'start': {'collectionkey' : f'substrate_{substrate}'},
                    f'measure_{0}':{'method': 'open_circuit_potentiometry',
                                    'parameters': json.dumps({'t_run': 2.5, 't_interval': 0.25}),
                                    'filename': 'substrate_{}_dummy_ocp_{}_{}'.format(substrate, 0, 0),
                                    'substrate': substrate,
                                    'id': 0,
                                    'experiment': 0},
                    f'measure_{1}':{'method': 'potentiostatic_impedance_spectroscopy',
                        'parameters': json.dumps({
                            "e_dc": 0.0,                 # DC potential
                            "e_ac": 0.01,                # AC potential (10 mV/s)
                            "n_frequencies": 41,         # Number of frequencies
                            "max_frequency": 1e5,        # Maximum frequency
                            "min_frequency": 1e1,        # Minimum frequency
                            "meas_vs_ocp_true": 1,       # Measure vs OCP
                            "t_max_ocp": 20.0,           # Maximum time OCP stabilization
                            "stability_criterion": 0.001 # Stability criterion in mV/s
                            }),
                        'filename': 'substrate_{}_dummy_peis_{}_{}'.format(substrate, 0, i),
                        'substrate': substrate,
                        'id': i,
                        'experiment': i},
                    f'measure_{2}':{'method': 'cyclic_voltammetry',
                        'parameters': json.dumps({"equilibration_time": 5,  # Equilibration time in seconds
                            "e_begin": 0.6,          # Begin potential in volts
                            "e_vtx1": 0.9,           # Vertex 1 potential in volts
                            "e_vtx2": 0.0,            # Vertex 2 potential in volts
                            "e_step": 0.01,           # Step potential in volts
                            "scan_rate": 0.1,   # Scan rate in V/s
                            "n_scans": 5             # Number of scans
                            }),
                        'filename': 'substrate_{}_dummy_cv_{}_{}'.format(substrate, 0, 0),
                                    'substrate': substrate,
                                    'id': 0,
                                    'experiment': 0},
                    f'moveHome_{0}':{}
                    },
            meta=dict()))



substrate = 1033
V=500
measurements = [
    ("NiHCF", {'V1': 0, 'V2': 0, 'V3': V/2, 'V4': V/2, 'V5': 0}),
    #("Ni0.8Mn0.2HCF", {'V1': 0, 'V2': 0, 'V3':0.8*V/2, 'V4': V/2, 'V5': 0.2*V/2})
    #("Ni0.6Mn0.4HCF", {'V1': 0, 'V2': 0, 'V3': 0.6*V/2, 'V4': V/2, 'V5': 0.4*V/2}),
    #("Ni0.4Mn0.6HCF", {'V1': 0, 'V2': 0, 'V3': 0.4*V/2, 'V4': V/2, 'V5': 0.6*V/2}),
    #("Ni0.2Mn0.8HCF", {'V1': 0, 'V2': 0, 'V3': 0.2*V/2, 'V4': V/2, 'V5': 0.8*V/2}),
    #("MnHCF", {'V1': 0, 'V2': 0, 'V3': 0, 'V4': V/2, 'V5': V/2})
]

test_fnc(dict(soe=[
            f'orchestrator/start', 
            f'dobot/moveHome_{measure_index}', 
            f'dobot/moveWaste_{measure_index}', 
            f'psd/pumpMix_{measure_index}', 
            f'psd/pumpVial_{measure_index}', 
            f'dobot/removeDrop_{measure_index}', 
        #    f'dobot/removeDrop_{measure_index+1}',
            f'dobot/moveSample_{measure_index}', 
            f'dobot/moveSample_{measure_index+1}',  
            f'dobot/moveDown_{measure_index}'
        ],
        params={
            'start': {'collectionkey': f'substrate_{substrate}'},
            f'moveHome_{measure_index}': {},
            f'moveWaste_{measure_index}': {'x': 0, 'y': 0, 'z': 0, 'r': 0},
            f'pumpMix_{measure_index}': {**pump_mix_volumes, 'V6': 0, 'speed': 20, 'mix': 1, 'times': 1, 'cell': False},
            f'pumpVial_{measure_index}': {'volume': 350, 'speed': 15, 'times': 1},
            f'removeDrop_{measure_index}': {'x': 0, 'y': 3.5, 'z': 0, 'r': 0},
         #   f'removeDrop_{measure_index+1}': {'x': 0, 'y': 3.5, 'z': 0, 'r': 0}, 
            f'moveSample_{measure_index}': {'x': 30, 'y': 40, 'z': 0, 'r': 0},
            f'moveSample_{measure_index+1}': {'x': 30, 'y': 40, 'z': -13.8, 'r': 0},
            f'moveDown_{measure_index}': {'dz': 0.05, 'steps': 50, 'maxForce': 200, 'threshold': 0.1},
            },
        meta=dict()))

### testing leakage

# 1 - dw
# 2 - se
substrate = -999

test_fnc(dict(soe=['orchestrator/start', f'dobot/moveHome_{0}', f'dobot/moveWaste_{0}', f'psd/pumpSimple_{0}', f'dobot/moveHome_{1}', 
                   f'dobot/removeDrop_{0}', f'dobot/removeDrop_{1}', f'dobot/removeDrop_{2}', f'psd/pumpSimple_{1}', f'dobot/moveSample_{0}', f'dobot/moveSample_{1}',
                   f'dobot/moveDown_{0}', f'psd/pumpVial_{0}', f'psd/pumpSimple_{2}',  f'psd/pumpVial_{1}', f'psd/pumpSimple_{3}', f'psd/pumpVial_{2}', f'palmsens/measure_{0}'], 
            params={'start': {'collectionkey' : f'substrate_{substrate}'},
                    f'moveHome_{0}':{},
                    f'moveWaste_{0}':{'x': 0, 'y':0, 'z': 0, 'r': 0},
                    f'pumpSimple_{0}': {'volume': 200, 'valve': 2, 'speed': 20, 'times': 2},
                    f'moveHome_{1}':{},
                    f'removeDrop_{0}': {'x': 0, 'y': 3.5, 'z': 0, 'r': 0},
                    f'removeDrop_{1}': {'x': 0, 'y': 3.5, 'z': 0, 'r': 0},
                    f'removeDrop_{2}': {'x': 0, 'y': 3.5, 'z': 0, 'r': 0},
                    f'pumpSimple_{1}': {'volume': -5, 'valve': 7, 'speed': 30, 'times': 1},
                    f'moveSample_{0}': {'x': 45, 'y': 49, 'z': 0, 'r': 0},
                    f'moveSample_{1}': {'x': 45, 'y': 49, 'z': -13.6, 'r': 0},
                    f'moveDown_{0}': {'dz': 0.05, 'steps': 50, 'maxForce': 200, 'threshold': 0.1},
                    f'pumpVial_{0}': {'volume': 20, 'speed': 30, 'times': 1},
                    f'pumpSimple_{2}': {'volume': -15, 'valve': 7, 'speed': 30, 'times': 1},
                    f'pumpVial_{1}': {'volume': 20, 'speed': 30, 'times': 1},
                    f'pumpSimple_{3}': {'volume': -15, 'valve': 7, 'speed': 30, 'times': 1},
                    f'pumpVial_{2}': {'volume': 20, 'speed': 30, 'times': 1},
                    f'measure_{0}':{'method': 'open_circuit_potentiometry',
                                    'parameters': json.dumps({'t_run': 30, 't_interval': 0.25}),
                                    'filename': 'substrate_{}_dummy_ocp_{}_{}'.format(substrate, -999, -999),
                                    'substrate': substrate,
                                    'id': -999,
                                    'experiment': -999}
                    },
            meta=dict()))

test_fnc(dict(soe=[f'psd/pumpSimple_{0}', f'dobot/moveJointRelative_{0}', f'psd/pumpSimple_{1}', f'dobot/moveJointRelative_{1}',
                   f'psd/pumpSimple_{2}', f'dobot/moveHome_{0}'], 
            params={f'pumpSimple_{0}': {'volume': -125, 'valve': 7, 'speed': 20, 'times': 1},
                    f'moveJointRelative_{0}':{'x': 0, 'y':0, 'z': 0.5, 'r': 0},
                    f'pumpSimple_{1}': {'volume': -125, 'valve': 7, 'speed': 20, 'times': 1},
                    f'moveJointRelative_{1}':{'x': 0, 'y':0, 'z': 0.5, 'r': 0},
                    f'pumpSimple_{2}': {'volume': -150, 'valve': 7, 'speed': 20, 'times': 1},
                    f'moveHome_{0}':{}
                    },
            meta=dict()))

test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))





test_fnc(dict(soe=['orchestrator/start', f'dobot/moveHome_{0}', f'dobot/moveWaste_{0}', f'psd/pumpSimple_{0}', f'force/read_{0}', f'palmsens/measure_{0}', 
                    f'dobot/moveHome_{1}'], 
            params={'start': {'collectionkey' : f'substrate_{substrate}'},
                    f'moveHome_{0}':{},
                    f'moveWaste_{0}':{'x': 0, 'y':0, 'z': 0, 'r': 0},
                    f'pumpSimple_{0}': {'volume': 200, 'valve': 2, 'speed': 10, 'times': 2},
                    f'read_{0}': {},
                    f'measure_{0}':{'method': 'open_circuit_potentiometry',
                                    'parameters': json.dumps({'t_run': 2.5, 't_interval': 0.25}),
                                    'filename': 'substrate_{}_dummy_ocp_{}_{}'.format(substrate, 0, 0),
                                    'substrate': substrate,
                                    'id': 0,
                                    'experiment': 0},
                    f'moveHome_{1}':{}
                    },
            meta=dict()))

test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))





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










