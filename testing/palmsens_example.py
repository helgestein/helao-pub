import sys
sys.path.append(r'C:/Users/juliu/helao-dev')
import action.palmsens_action as echem_action



echem_action.measure(
    callback_func=None,
    sampleName="test_sample",
    method="electrochemical_impedance_spectroscopy",
    parameters={
        "scan_type": 2,
        "freq_type": 1,
        "equilibration_time": 10.,
        "e_dc": 0.0,
        "e_ac": 0.01,
        "n_frequencies": 13,
        "max_frequency": 1e5,
        "min_frequency": 1e4
        }
)

echem_action.measure(
    callback_func=None,
    sampleName="test_sample_cv",
    method="cyclic_voltammetry",
    parameters={
        'e_begin': 0.0,
        'e_vtx1': -0.5,
        'e_vtx2': 0.5,
        'e_step': 0.01,
        'scan_rate': 0.05,
        'n_scans': 5
        }
)

echem_action.measure(
    callback_func=None,
    sampleName="test_sample_cv",
    method="multiple_pulse_amperometry",
    parameters={
        'e1': 0.5,
        't1': 5,
        'e2': -0.5,
        't2': 5
        }
)

echem_action.measure(
    callback_func=None,
    sampleName="test_sample_ocp",
    method="ocp",
    parameters={
        't_interval': 0.05,
        't_run': 8
        }
)

echem_action.measure(
    callback_func=None,
    sampleName="test_sample_cp",
    method="chronopotentiometry",
    parameters={
        'current': 0.0002,
        't_interval': 0.01,
        't_run': 5
        }
)

echem_action.measure(
    callback_func=None,
    sampleName="test_sample_cp",
    method="differential_pulse_voltammetry",
    parameters={
        'e_begin': 0.1,
        'e_end': -0.4,
        'e_step': 0.01,
        'scan_rate': 0.05,
        'e_pulse': 0.1,
        't_pulse': 0.02
        }
)


echem_action.measure(
    callback_func=None,
    sampleName="test_sample_cp",
    method="square_wave_voltammetry",
    parameters={
        'e_begin': 0.1,
        'e_end': -0.4,
        'e_step': 0.01,
        'amplitude': 0.01,
        'frequency': 10
        }
)