import requests
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
import time
import json
from config.sdc_cyan import config

def echem_test(action, params):
    server = 'palmsens'
    action = action
    params = params
    res = requests.get("http://{}:{}/{}/{}".format(
        config['servers']['palmsens']['host'], 
        config['servers']['palmsens']['port'], server, action),
        params= params).json()
    return res

#echem_test('measure', params=dict(method= "open_circuit_potentiometry", parameters= '{"t_run": 1, "t_interval": 0.5}', filename= "dummy_cell_test_ocp_1"))

echem_test('measure', params=dict(method="open_circuit_potentiometry", 
                                  parameters= json.dumps({"t_run": 5.0,             # Measurement ime in seconds
                                                          "t_interval": 0.5         # Time interval in seconds
                                                          }), 
                                  filename= "dummy_cell_test_ocp_0"))

echem_test('measure', params=dict(method="chronopotentiometry", 
                                  parameters=json.dumps({"i": -5e-6,               # Current in Amps
                                                        "t_interval": 0.2,           # Interval time in seconds
                                                        "t_run": 5.0,                # Run time in seconds
                                                        "e_max": 0.5,                # Max potential limit
                                                        "e_min": -0.5,               # Min potential limit
                                                        "e_max_bool": False,          # Whether to use max limit
                                                        "e_min_bool": False          # Whether to use min limit 
                                                        }),
                                  filename="dummy_cell_test_substrate_1037_charge_cp_0"))

echem_test('measure', params=dict(method="linear_sweep_potentiometry",
                                 parameters=json.dumps({"i_input_range": -5,         # Start current range (in log10(A))
                                                        "i_begin": -1.0,             # Start current
                                                        "i_end": 1.0,                # End current
                                                        "i_step": 0.01,              # Current step
                                                        "scan_rate": 1.0             # Scan rate
                                                        }),
                                 filename="dummy_cell_test_lcp_0"))

echem_test('measure', params=dict(method="linear_sweep_voltammetry",
                                 parameters=json.dumps({"e_begin": -0.5,           # Begin potential in volts
                                                        "e_end": 0.5,              # End potential in volts
                                                        "e_step": 0.02,            # Step potential in volts
                                                        "scan_rate": 0.5           # Scan rate in V/s}),
                                                        }),
                                 filename="dummy_cell_test_lcv_0"))

echem_test('measure', params=dict(method="cyclic_voltammetry",
                                 parameters=json.dumps({"equilibration_time": 0,  # Equilibration time in seconds
                                                        "e_begin": -0.5,          # Begin potential in volts
                                                        "e_vtx1": -1.0,           # Vertex 1 potential in volts
                                                        "e_vtx2": 1.0,            # Vertex 2 potential in volts
                                                        "e_step": 0.01,           # Step potential in volts
                                                        "scan_rate": 0.2,         # Scan rate in V/s
                                                        "n_scans": 3              # Number of scans
                                                        }),
                                 filename="dummy_cell_test_cv_0"))

echem_test('measure', params=dict(method="differential_pulse_voltammetry",
                                 parameters=json.dumps({"e_begin": -0.5,        # Begin potential in volts
                                                        "e_end": 0.5,           # End potential in volts
                                                        "e_step": 0.01,         # Step potential in volts
                                                        "scan_rate": 0.1,       # Scan rate in V/s
                                                        "e_pulse": 0.2,         # Pulse potential in volts
                                                        "t_pulse": 0.02         # Pulse time in seconds
                                                    }),
                                 filename="dummy_cell_test_dpv_0"))

echem_test('measure', params=dict(method="square_wave_voltammetry",
                                 parameters=json.dumps({"e_begin": -0.25,       # Begin potential in volts
                                                        "e_end": 0.5,           # End potential in volts
                                                        "e_step": 0.01,         # Step potential in volts
                                                        "amplitude": 0.1,       # Pulse amplitude in volts
                                                        "frequency": 20         # Frequency in Hz
                                                    }),
                                 filename="dummy_cell_test_swv_0"))

echem_test('measure', params=dict(method="normal_wave_voltammetry",
                                 parameters=json.dumps({"e_begin": -0.5,        # Begin potential in volts
                                                        "e_end": 0.5,           # End potential in volts
                                                        "e_step": 0.01,         # Step potential in volts
                                                        "scan_rate": 0.1,       # Scan rate in V/s
                                                        "t_pulse": 0.02         # Pulse time in seconds
                                                    }),
                                 filename="dummy_cell_test_ca_0"))

echem_test('measure', params=dict(method="normal_wave_voltammetry",
                                 parameters=json.dumps({"e_begin": -0.5,        # Begin potential in volts
                                                        "e_end": 0.5,           # End potential in volts
                                                        "e_step": 0.01,         # Step potential in volts
                                                        "scan_rate": 0.1,       # Scan rate in V/s
                                                        "t_pulse": 0.02         # Pulse time in seconds
                                                    }),
                                 filename="dummy_cell_test_ca_0"))

echem_test('measure', params=dict(method="chronoamperometry", 
                                  parameters=json.dumps({"e_applied": 0.5,             # Applied potential in volts
                                                        "interval_time": 0.1,          # Interval time in seconds
                                                        "run_time": 5.0,               # Total run time in seconds
                                                         }), 
                                  filename="dummy_cell_test_ca_0"))

echem_test('measure', params=dict(method="multiple_pulse_amperometry", 
                                  parameters=json.dumps({"e1": 0.1,                    # Potential for phase 1 in volts
                                                        "e2": 0.2,                    # Potential for phase 2 in volts
                                                        "e3": 0.3,                    # Potential for phase 3 in volts
                                                        "t1": 0.2,                    # Time for phase 1 in seconds
                                                        "t2": 0.5,                    # Time for phase 2 in seconds
                                                        "t3": 0.3,                    # Time for phase 3 in seconds
                                                        "run_time": 10.0,             # Total run time in seconds
                                                         }), 
                                  filename="dummy_cell_test_ca_0"))

echem_test('measure', params=dict(method="chronocoulometry", 
                                  parameters=json.dumps({"e_step_1": 0.5,             # First step potential
                                                        "e_step_2": -0.5,             # Second step potential
                                                        "t_1": 5.0,                   # Time for first step
                                                        "t_2": 5.0,                   # Time for second step
                                                        "interval_time": 0.1          # Interval time
                                                         }), 
                                  filename="dummy_cell_test_cc_0"))

echem_test('measure', params=dict(method="potentiostatic_impedance_spectroscopy",     # Fixed (standard)   
                                  parameters=json.dumps({"e_dc": 0.0,                 # DC potential
                                                         "e_ac": 0.01,                # AC potential (10 mV/s)
                                                         "n_frequencies": 11,         # Number of frequencies
                                                         "max_frequency": 1e5,        # Maximum frequency
                                                         "min_frequency": 1e4,        # Minimum frequency
                                                         "meas_vs_ocp_true": 1,       # Measure vs OCP
                                                         "t_max_ocp": 20.0,           # Maximum time OCP stabilization
                                                         "stability_criterion": 0.001, # Stability criterion in mV/s
                                                         "max_equilibration_time": 5.0, # Maximum equilibration time, optional
                                                         "sampling_time": 0.5         # Sampling time, optional
                                                         }), 
                                  filename="dummy_cell_test_peis_0"))

echem_test('measure', params=dict(method="galvanostatic_impedance_spectroscopy",    # Fixed (standard)
                                  parameters=json.dumps({"i_input_range": -4,       # DC current range
                                                         "i_dc": 0.1,               # DC current * range
                                                         "i_ac": 0.01,              # AC current * range
                                                         "n_frequencies": 31,       # Number of frequencies
                                                         "max_frequency": 5e4,      # Maximum frequency
                                                         "min_frequency": 5e1,       # Minimum frequency
                                                         "max_equilibration_time": 5.0, # Maximum equilibration time, optional
                                                         "sampling_time": 0.5         # Sampling time, optional
                                                         }), 
                                  filename="dummy_cell_test_geis_0"))

### advanced techniques

echem_test('measure', params=dict(method="potentiostatic_impedance_spectroscopy",     
                                  parameters=json.dumps({"scan_type": 1,              # Time scan
                                                         "e_dc": 0.0,                 # DC potential
                                                         "e_ac": 0.01,                # AC potential (10 mV/s)
                                                         "t_interval": 30,            # Time interval
                                                         "t_run": 60,                 # Run time
                                                         "n_frequencies": 11,         # Number of frequencies
                                                         "max_frequency": 1e5,        # Maximum frequency
                                                         "min_frequency": 1e4,        # Minimum frequency
                                                         "meas_vs_ocp_true": 1,       # Measure vs OCP
                                                         "t_max_ocp": 20.0,           # Maximum time OCP stabilization
                                                         "stability_criterion": 0.001, # Stability criterion in mV/s
                                                         "max_equilibration_time": 5.0, # Maximum equilibration time, optional
                                                         "sampling_time": 0.5,         # Sampling time, optional
                                                         "record_aux_input": True     # Record auxiliary input
                                                         }), 
                                  filename="dummy_cell_test_peis_1"))

echem_test('measure', params=dict(method="potentiostatic_impedance_spectroscopy",     
                                  parameters=json.dumps({"scan_type": 0,              # Potential scan
                                                         "e_begin": 0.0,              # BeginPotential (V)
                                                         "e_step": 0.1,               # Step potential (V)
                                                         "e_end": 0.5,                # End potential (V)
                                                         "e_ac": 0.01,                # AC potential (10 mV/s)
                                                         "t_interval": 30.0,          # Time interval
                                                         "t_run": 60.0,                # Run time
                                                         "n_frequencies": 11,         # Number of frequencies
                                                         "max_frequency": 1e5,        # Maximum frequency
                                                         "min_frequency": 1e4,        # Minimum frequency
                                                         "meas_vs_ocp_true": 1,       # Measure vs OCP
                                                         "t_max_ocp": 20.0,           # Maximum time OCP stabilization
                                                         "stability_criterion": 0.001, # Stability criterion in mV/s
                                                         "max_equilibration_time": 5.0, # Maximum equilibration time, optional
                                                         "sampling_time": 0.5,         # Sampling time, optional
                                                         "record_aux_input": False     # Record auxiliary input
                                                         }), 
                                  filename="dummy_cell_test_peis_0"))

echem_test('measure', params=dict(method="galvanostatic_impedance_spectroscopy", 
                                  parameters=json.dumps({"scan_type": 1,            # Time scan
                                                         "i_input_range": -4,       # DC current range
                                                         "i_dc": 0.1,               # DC current * range
                                                         "i_ac": 0.01,              # AC current * range
                                                         "t_interval": 60.0,        # Time interval
                                                         "t_run": 3600.0,           # Run time
                                                         "n_frequencies": 31,       # Number of frequencies
                                                         "max_frequency": 5e4,      # Maximum frequency
                                                         "min_frequency": 5e1,      # Minimum frequency
                                                         "max_equilibration_time": 5.0, # Maximum equilibration time, optional
                                                         "sampling_time": 0.5,         # Sampling time, optional
                                                         "record_aux_input": False     # Record auxiliary input
                                                         }), 
                                  filename="dummy_cell_test_geis_0"))

echem_test('measure', params=dict(method="galvanostatic_impedance_spectroscopy", 
                                  parameters=json.dumps({"scan_type": 0,            # Current scan
                                                         "i_input_range": -4,       # DC current range
                                                         "i_begin": 0.0,            # DC current begin * range
                                                         "i_step": 0.1,             # DC current step * range
                                                         "i_end": 0.5,              # DC current end * range
                                                         "i_ac": 0.01,              # AC current * range
                                                         "t_interval": 30.0,        # Time interval
                                                         "t_run": 50.0,             # Run time
                                                         "n_frequencies": 31,       # Number of frequencies
                                                         "max_frequency": 5e4,      # Maximum frequency
                                                         "min_frequency": 5e1,      # Minimum frequency
                                                         "max_equilibration_time": 5.0, # Maximum equilibration time, optional
                                                         "sampling_time": 0.5,         # Sampling time, optional
                                                         "record_aux_input": False     # Record auxiliary input
                                                         }), 
                                  filename="dummy_cell_test_geis_0"))

echem_test('measure', params=dict(method="cyclic_voltammetry",
                                 parameters=json.dumps({"equilibration_time": 0,            # Equilibration time in seconds
                                                        "e_begin": -0.5,                    # Begin potential in volts
                                                        "e_vtx1": -1.0,                     # Vertex 1 potential in volts
                                                        "e_vtx2": 1.0,                      # Vertex 2 potential in volts
                                                        "e_step": 0.01,                     # Step potential in volts
                                                        "scan_rate": 0.2,                   # Scan rate in V/s
                                                        "n_scans": 1,                       # Number of scans
                                                        "use_ir_drop_compensation": True,  # Use IR drop compensation
                                                        "ir_comp_resistance": 100.0,          # IR compensation resistance in Ohms
                                                        "record_aux_input": False,          # Record auxiliary input
                                                        "record_cell_potential": False,     # Record cell potential
                                                        "record_we_potential": False        # Record working electrode potential
                                                        }),
                                 filename="dummy_cell_test_cv_0"))
