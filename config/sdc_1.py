config = dict()

config['servers'] = dict(pumpServer=dict(host="127.0.0.1", port=13370),
                         pumpingServer=dict(host="127.0.0.1", port=13371),
                         mecademicServer=dict(host="127.0.0.1", port=13372),
                         movementServer=dict(host="127.0.0.1", port=13373),
                         autolabServer=dict(host="127.0.0.1", port=13394),
                         echemServer=dict(host="127.0.0.1", port=13375),
                         kadiServer=dict(host="127.0.0.1", port=13376),
                         dataServer=dict(host="127.0.0.1", port=13377),
                         megsvServer=dict(host="127.0.0.1", port=13378),
                         sensingServer=dict(host="127.0.0.1", port=13379),
                         orchestrator=dict(host="127.0.0.1", port=13380),
                         motorServer=dict(host="127.0.0.1", port=13381),
                         langServer=dict(host="127.0.0.1", port=13382),
                         oceanServer=dict(host="127.0.0.1", port=13383),
                         smallRamanServer=dict(host="127.0.0.1", port=13384),
                         arcoptixServer=dict(host="127.0.0.1", port=13385),
                         ftirServer=dict(host="127.0.0.1", port=13386),
                         owisServer=dict(host="127.0.0.1", port=13387),
                         tableServer=dict(host="127.0.0.1", port=13388),
                         minipumpServer=dict(host="127.0.0.1", port=13389),
                         minipumpingServer=dict(host="127.0.0.1", port=13344),
                         measureServer=dict(host="127.0.0.1", port=13368),
                         analysisServer=dict(host="127.0.0.1", port=13369),
                         learningServer=dict(host="127.0.0.1", port=13363))

config['kadi'] = dict(host=r"https://polis-kadi4mat.iam-cms.kit.edu",
                      PAT=r"78ac200f0379afb4873c7b0ee71f5489946158fe882466a9", group='2')


config['pump'] = dict(port='COM4', baud=9600, timeout=0.1, pumpAddr={i: i + 21 for i in range(14)})  # numbering is left to right top to bottom
config['pump']['pumpAddr'].update({i: i for i in range(20, 35)})
config['pump']['pumpAddr']['all'] = 20

config['autolab'] = dict(basep=r"C:\Program Files\Metrohm Autolab\Autolab SDK 1.11",
                         procp=r"C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\config\echemprocedures",
                         #hwsetupf = r"C:\ProgramData\Metrohm Autolab\12.0\HardwareSetup.AUT88172.xml",
                         hwsetupf=r"C:\ProgramData\Metrohm Autolab\12.0\HardwareSetup.AUT88078.xml",
                         micsetupf=r"C:\Program Files\Metrohm Autolab\Autolab SDK 1.11\Hardware Setup Files\Adk.bin",
                         proceuduresd={'cp': r'C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\config\echemprocedures\CP.nox',
                                       'ca': r'C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\config\echemprocedures\CA_corrected.nox',
                                       'cv': r'C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\config\echemprocedures\CV.nox',
                                       'eis': r'C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\config\echemprocedures\eis_fast_final.nox',
                                       'ocp': r'C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\config\echemprocedures\ocp_signal.nox',
                                       'on': r'C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\config\echemprocedures\ON.nox',
                                       'off': r'C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\config\echemprocedures\OFF.nox',
                                       'ocp_rf': r"C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\config\echemprocedures\ocp_rf_v12.nox",
                                       'ms': r'C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\config\echemprocedures\mott_schotky_no_osc.nox',
                                       'pitt' : r'C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\config\echemprocedures\PITT.nox',
                                       'gitt' : r'C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\config\echemprocedures\GITT.nox',
                                       'gitt_eis' : r'C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\config\echemprocedures\GITT_EIS.nox'})

config['echem'] = dict(procedures=dict())

config['echem']['procedures']['ca'] = {'procedure': 'ca',
                                       'setpoints': {'applypotential': {'Setpoint value': 0.735},
                                                     'recordsignal': {'Duration': 1000}},
                                       'plot': 'tCV',
                                       'onoffafter': 'off',
                                       'safepath': r"C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\temp",
                                       'filename': 'ca.nox',
                                       'parseinstructions': ['recordsignal']}


config['echem']['procedures']['ocp'] = {'procedure': 'ocp',
                                        'setpoints': {'FHLevel': {'Duration': 20}},
                                        'plot': 'tCV',
                                        'onoffafter': 'off',
                                        'safepath': r"C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\temp",
                                        'filename': 'ocp.nox',
                                        'parseinstructions': ['FHLevel']}

config['echem']['procedures']['ms'] = {'procedure': 'ms',
                                       # 'setpoints': {'ExecCommandForeach': 'FIAMeasPotentiostatic': {} },
                                       'setpoints': {'FHSetSetpointPotential': {'Setpoint value': 0.01}},
                                       'plot': 'impedance',
                                       'onoffafter': 'off',
                                       'safepath': r"C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\temp",
                                       'filename': 'ms.nox',
                                       'parseinstructions': ["FIAMeasurement", "FHLevel"]}


config['echem']['procedures']['ocp_rf'] = {'procedure': 'ocp_rf',
                                           'setpoints': {'FHRefDetermination': {'Timeout': 20}},
                                           'plot': 'tCV',
                                           'onoffafter': 'off',
                                           'safepath': r"C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\temp",
                                           'filename': 'ocp_rf.nox',
                                           'parseinstructions': ['OCP determination']}


config['echem']['procedures']['cp'] = {'procedure': 'cp',
                                       'setpoints': {'applycurrent': {'Setpoint value': 7*(10**-6)},
                                                     'recordsignal': {'Duration': 600}},
                                       'plot': 'tCV',
                                       'onoffafter': 'off',
                                       'safepath': r"C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\temp",
                                       'filename': 'cp.nox',
                                       'parseinstructions': ['recordsignal']}

config['echem']['procedures']['cv'] = {'procedure': 'cv',
                                       'setpoints': {
                                           'FHSetSetpointPotential': {'Setpoint value': 0.4},
                                           'FHWait': {'Time': 2},
                                           'CVLinearScanAdc164': {'StartValue': 0.4,
                                                                  'UpperVertex': 1.5,
                                                                  'LowerVertex': 0.399,
                                                                  'NumberOfStopCrossings': 50,
                                                                  'ScanRate': 0.02}},
                                       'plot': 'tCV',
                                       'onoffafter': 'off',
                                       'safepath': r"C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\temp",
                                       'filename': 'cv.nox',
                                       'parseinstructions': ['CVLinearScanAdc164']}

config['echem']['procedures']['eis'] = {'procedure': 'eis',
                                        'setpoints': {'FHSetSetpointPotential': {'Setpoint value': 0.01}},
                                        'plot': 'impedance',
                                        'onoffafter': 'off',
                                        'safepath': r"C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\temp",
                                        'filename': 'eis.nox',
                                        'parseinstructions': ['FIAMeasPotentiostatic']}

config['echem']['procedures']['pitt'] = {'procedure': 'pitt',
                                        'setpoints': {
                                            'OCP determination': {'Timeout': 60},
                                            # charge loop range list list(proc.Commands['Charge loop'].CommandParameters['Values'].Value.RangeCollection)
                                            'Charge pulse': {'Duration': 600},
                                            'Charge relaxation': {'Duration': 600},
                                            'Discharge pulse': {'Duration': 600},
                                            'Discharge relaxation': {'Duration': 600},
                                            'Export ASCII data': {'Filename': r'C:\Users\LaborRatte_23_3\Documents\My Procedures 1.11\pitt.txt'}},
                                        'plot': 'impedance',
                                        'onoffafter': 'off',
                                        'safepath': r"C:\Users\SDC_1\Documents\Github\helao-dev\temp",
                                        'filename': 'eis.nox',
                                        'parseinstructions': ['FIAMeasPotentiostatic']}

config['echem']['procedures']['gitt'] = {'procedure': 'gitt',
                                        'setpoints': {
                                            'Autolab control': {'WE(1).Current range': -2}, # 1=10A, 0=1A, -1=100mA, -2=10mA, -3=1mA, -4=100uA, -5=10uA, -6=1uA, -7=100nA, -8=10nA
                                            'OCP determination': {'Timeout': 10},
                                            'Charge loop': {'Number of repetitions': 78}, 
                                            'Set charge current': {'Current (A)': 0.005},
                                            'Charge pulse': {'Duration': 600}, #cutoff is missing
                                            'Charge relaxation': {'Duration': 600},
                                            'Discharge loop': {'Number of repetitions': 78},
                                            'Set charge current': {'Current (A)': -0.005},
                                            'Discharge pulse': {'Duration': 600}, #cutoff is missing
                                            'Discharge relaxation': {'Duration': 600},
                                            'Export ASCII data': {'Filename': r'C:\Users\LaborRatte_23_3\Documents\My Procedures 1.11\pitt.txt'}},
                                        'plot': 'impedance',
                                        'onoffafter': 'off',
                                        'safepath': r"C:\Users\SDC_1\Documents\Github\helao-dev\temp",
                                        'filename': 'eis.nox',
                                        'parseinstructions': ['FIAMeasPotentiostatic']}

config['echem']['procedures']['gitt_eis'] = {'procedure': 'gitt_eis',
                                        'setpoints': {
                                            'Autolab control 1': {'WE(1).Current range': -2},  # 1=10A, 0=1A, -1=100mA, -2=10mA, -3=1mA, -4=100uA, -5=10uA, -6=1uA, -7=100nA, -8=10nA
                                            'OCP determination 1': {'Timeout': 30},
                                            'Charge loop': {'Number of repetitions': 78}, 
                                            'Charge current': {'Current (A)': 0.005},
                                            'Charge pulse': {'Duration': 600}, #cutoff is missing
                                            'Charge relaxation': {'Duration': 600},
                                            'OCP determination 2': {'Timeout': 30},
                                            #FRA measurement settings
                                            'Discharge loop': {'Number of repetitions': 78},
                                            'Discharge current': {'Current (A)': -0.005},
                                            'Discharge pulse': {'Duration': 600}, #cutoff is missing
                                            'Discharge relaxation': {'Duration': 600},
                                            'OCP determination 3': {'Timeout': 30},
                                            #FRA measurement settings
                                            'Export ASCII data': {'Filename': r'C:\Users\LaborRatte_23_3\Documents\My Procedures 1.11\pitt.txt'}},
                                        'plot': 'impedance',
                                        'onoffafter': 'off',
                                        'safepath': r"C:\Users\SDC_1\Documents\Github\helao-dev\temp",
                                        'filename': 'eis.nox',
                                        'parseinstructions': ['FIAMeasPotentiostatic']}

config['lang'] = dict(vx=5, vy=5, vz=5, port='COM3',
                      dll=r"C:\Users\LaborRatte23-3\Documents\git\pyLang\LStepAPI\_C#_VB.net\CClassLStep64",
                      dllconfig=r"C:\Users\LaborRatte23-3\Documents\git\pyLang\config.LSControl",
                      safe_home_pos=[0.0, 0.0, 0.0],
                      # 60.0, 70.0, -6.1348, #2.0, 85.0, 0.0
                      safe_waste_pos=[3.0, -31.0, 0.0],
                      safe_sample_pos=[3.0, 4.0, 0.0],
                      remove_drop=[3.0, -15.0, 9.5]) 

config['megsv'] = dict(port=5,
                       buffer_size=1,
                       dll_address=r"C:\Users\LaborRatte23-3\Desktop\megsv\megsv_x64\MEGSV.dll")

config['minipump'] = dict(port='COM4', baud=1200, timeout=1)

config['orchestrator'] = dict(path=r'C:\Users\LaborRatte23-3\Documents\data')


config['launch'] = dict(server = ['autolab_server','kadi_server','lang_server','megsv_server', 'minipump_server', 'pump_server'],
                        action = ['analysis_action','echem_ocean','kadi_action','lang_action', 'learning_action', 'measure_action', 'minipumping_action', 'ml_action', 'pumping_action', 'sensing_mesgsv'],
                        orchestrator = ['mischbares'],
                        visualizer = ['autolab_visualizer'],
                        process = [])


