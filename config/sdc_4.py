config = dict()

config['servers'] = dict(pumpDriver=dict(host="127.0.0.1", port=13370),
                         pump=dict(host="127.0.0.1", port=13371),
                         autolabDriver=dict(host="127.0.0.1", port=13374),
                         autolab=dict(host="127.0.0.1", port=13375),
                         kadiDriver=dict(host="127.0.0.1", port=13376),
                         kadi=dict(host="127.0.0.1", port=13377),
                         forceDriver=dict(host="127.0.0.1", port=13378),
                         force=dict(host="127.0.0.1", port=13379),
                         orchestrator=dict(host="127.0.0.1", port=13380),
                         langDriver=dict(host="127.0.0.1", port=13382),
                         lang=dict(host="127.0.0.1", port=13391),
                         minipumpDriver=dict(host="127.0.0.1", port=13386),
                         minipump=dict(host="127.0.0.1", port=13385),
                         analysis=dict(host="127.0.0.1", port=13369),
                         ml=dict(host="127.0.0.1", port=13363))

#config['servers'] = {'analysis': dict(host="192.168.31.123", port=6642),
#                     'ml': dict(host="192.168.31.123", port=6612)}
                        
#config['servers'].update({'measure:1':dict(host="192.168.31.123", port=6667), # fume hood pc 
#                         'measure:2':dict(host="192.168.31.114", port=6669)}) # raman pc

#config['measure:1'] = dict(url="http://192.168.31.123:6667")
#config['measure:2'] = dict(url="http://192.168.31.114:6669")
#config['analysis'] = dict(url="http://192.168.31.123:6642")
#config['ml'] = dict(url="http://192.168.31.123:6612")


config['kadiDriver'] = dict(host=r"https://polis-kadi4mat.iam-cms.kit.edu",
                            PAT=r"78ac200f0379afb4873c7b0ee71f5489946158fe882466a9")

config['kadi'] = dict(group='2', url="http://127.0.0.1:13376")


#config['pumpDriver'] = dict(port='COM4', baud=9600, timeout=0.1, pumpAddr={
#                            i: i + 21 for i in range(14)})  # numbering is left to right top to bottom
#config['pumpDriver']['pumpAddr'].update({i: i for i in range(20, 35)})
#config['pumpDriver']['pumpAddr']['all'] = 20

#config['pump'] = dict(url="http://127.0.0.1:13370")

config['autolabDriver'] = dict(basep = r"C:\Program Files\Metrohm Autolab\Autolab SDK 1.11",
                    procp = r"C:\Users\LaborRatte23-2\Documents\echemprocedures",
                    #hwsetupf = r"C:\ProgramData\Metrohm Autolab\12.0\HardwareSetup.AUT88172.xml",
                    hwsetupf = r"C:\ProgramData\Metrohm Autolab\12.0\HardwareSetup.AUT88172.xml",
                    micsetupf = r"C:\Program Files\Metrohm Autolab\Autolab SDK 1.11\Hardware Setup Files\Adk.bin",
                    proceuduresd = {'cp': r'C:\Users\LaborRatte23-2\Documents\echemprocedures\CP.nox',      
                                    'ca': r'C:\Users\LaborRatte23-2\Documents\echemprocedures\CA.nox',
                                    'cv': r'C:\Users\LaborRatte23-2\Documents\echemprocedures\CV.nox',
                                    'eis': r'C:\Users\LaborRatte23-2\Documents\echemprocedures\eis_fast_final.nox',
                                    'ocp': r'C:\Users\LaborRatte23-2\Documents\echemprocedures\ocp_signal.nox',
                                    'on': r'C:\Users\LaborRatte23-2\Documents\echemprocedures\ON.nox',
                                    'off': r'C:\Users\LaborRatte23-2\Documents\echemprocedures\OFF.nox', 
                                    'ocp_rf': r"C:\Users\LaborRatte23-2\Documents\echemprocedures\ocp_rf_v12.nox",
                                    'ms': r'C:\Users\LaborRatte23-2\Documents\echemprocedures\mott_schotky_no_osc.nox',
                                    "eis_v2": r"C:\Users\LaborRatte23-2\Documents\My Procedures 1.11\Procedures\FRA impedance potentiostatic working electrode.nox",
                                    "cccv":r"C:\Users\LaborRatte23-2\Documents\My Procedures 1.11\Procedures\cccv.nox"})

config['autolab'] = dict(url="http://127.0.0.1:13374")
config['autolab']['procedures'] = {}

config['autolab']['procedures']['ca'] = {'procedure': 'ca',
                                               'setpoints': {'applypotential': {'Setpoint value': 0.735},
                                                             'recordsignal': {'Duration': 1000}},
                                               'plot': 'tCV',
                                               'onoffafter': 'off',
                                               'safepath': r"C:\Users\LaborRatte23-2\Documents\GitHub\helao-dev\temp",
                                               'filename': 'ca.nox',
                                               'parseinstructions': ['recordsignal']}
### every thing would be the same except setpoints
# ['ExtendedSequence',
#  'FHGetSetValues',
#  'FHWait',
#  'FHSetSetpointCurrent',
#  'FHSwitchCell',
#  'FHLevelGalvanostatic',
#  'PlotsEvst',
#  'FHSetSetpointCurrent',
#  'FHLevelGalvanostatic',
#  'PlotsEvst',
#  'FHSwitchCell']
config['autolab']['procedures']['cccv'] = {'setpointsjson':{'FHSetSetpointCurrent': {'Setpoint value': 1e-06}}}

config['autolab']['procedures']['ocp'] = {'procedure': 'ocp',
                                                'setpoints': {'FHLevel': {'Duration': 20}},
                                                'plot': 'tCV',
                                                'onoffafter': 'off',
                                                'safepath': r"C:\Users\LaborRatte23-2\Documents\GitHub\helao-dev\temp",
                                                'filename': 'ocp.nox',
                                                'parseinstructions': ['FHLevel']}

config['autolab']['procedures']['ms'] = {'procedure': 'ms',
                                               # 'setpoints': {'ExecCommandForeach': 'FIAMeasPotentiostatic': {} },
                                               'setpoints': {'FHSetSetpointPotential': {'Setpoint value': 0.01}},
                                               'plot': 'impedance',
                                               'onoffafter': 'off',
                                               'safepath': r"C:\Users\LaborRatte23-2\Documents\GitHub\helao-dev\temp",
                                               'filename': 'ms.nox',
                                               'parseinstructions': ["FIAMeasurement", "FHLevel"]}


config['autolab']['procedures']['ocp_rf'] = {'procedure': 'ocp_rf',
                                                   'setpoints': {'FHRefDetermination': {'Timeout': 20}},
                                                   'plot': 'tCV',
                                                   'onoffafter': 'off',
                                                   'safepath': r"C:\Users\LaborRatte23-2\Documents\GitHub\helao-dev\temp",
                                                   'filename': 'ocp_rf.nox',
                                                   'parseinstructions': ['OCP determination']}


config['autolab']['procedures']['cp'] = {'procedure': 'cp',
                                               'setpoints': {'applycurrent': {'Setpoint value': 7*(10**-6)},
                                                             'recordsignal': {'Duration': 600}},
                                               'plot': 'tCV',
                                               'onoffafter': 'off',
                                               'safepath': r"C:\Users\LaborRatte23-2\Documents\GitHub\helao-dev\temp",
                                               'filename': 'cp.nox',
                                               'parseinstructions': ['recordsignal']}

config['autolab']['procedures']['cv'] = {'procedure': 'cv',
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
                                               'safepath': r"C:\Users\LaborRatte23-2\Documents\GitHub\helao-dev\temp",
                                               'filename': 'cv.nox',
                                               'parseinstructions': ['CVLinearScanAdc164']}

config['autolab']['procedures']['eis'] = {'procedure': 'eis',
                                                'setpoints': {'FHSetSetpointPotential': {'Setpoint value': 0.01}},
                                                'plot': 'impedance',
                                                'onoffafter': 'off',
                                                'safepath': r"C:\Users\LaborRatte23-2\Documents\GitHub\helao-dev\temp",
                                                'filename': r'C:\Users\LaborRatte23-2\Documents\My Procedures 1.11\Procedures\FRA_impedance_potentiostatic_WE_CE_RE.nox',
                                                'parseinstructions': ['FIAMeasPotentiostatic']}

config['autolab']['procedures']['pitt'] = {'procedure': 'pitt',
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

config['autolab']['procedures']['gitt'] = {'procedure': 'gitt',
                                                 'setpoints': {
                                                     # 1=10A, 0=1A, -1=100mA, -2=10mA, -3=1mA, -4=100uA, -5=10uA, -6=1uA, -7=100nA, -8=10nA
                                                     'Autolab control': {'WE(1).Current range': -2},
                                                     'OCP determination': {'Timeout': 10},
                                                     'Charge loop': {'Number of repetitions': 78},
                                                     'Set charge current': {'Current (A)': 0.005},
                                                     # cutoff is missing
                                                     'Charge pulse': {'Duration': 600},
                                                     'Charge relaxation': {'Duration': 600},
                                                     'Discharge loop': {'Number of repetitions': 78},
                                                     'Set charge current': {'Current (A)': -0.005},
                                                     # cutoff is missing
                                                     'Discharge pulse': {'Duration': 600},
                                                     'Discharge relaxation': {'Duration': 600},
                                                     'Export ASCII data': {'Filename': r'C:\Users\LaborRatte_23_3\Documents\My Procedures 1.11\pitt.txt'}},
                                                 'plot': 'impedance',
                                                 'onoffafter': 'off',
                                                 'safepath': r"C:\Users\SDC_1\Documents\Github\helao-dev\temp",
                                                 'filename': 'eis.nox',
                                                 'parseinstructions': ['FIAMeasPotentiostatic']}

config['autolab']['procedures']['gitt_eis'] = {'procedure': 'gitt_eis',
                                                     'setpoints': {
                                                         # 1=10A, 0=1A, -1=100mA, -2=10mA, -3=1mA, -4=100uA, -5=10uA, -6=1uA, -7=100nA, -8=10nA
                                                         'Autolab control 1': {'WE(1).Current range': -2},
                                                         'OCP determination 1': {'Timeout': 30},
                                                         'Charge loop': {'Number of repetitions': 78},
                                                         'Charge current': {'Current (A)': 0.005},
                                                         # cutoff is missing
                                                         'Charge pulse': {'Duration': 600},
                                                         'Charge relaxation': {'Duration': 600},
                                                         'OCP determination 2': {'Timeout': 30},
                                                         # FRA measurement settings
                                                         'Discharge loop': {'Number of repetitions': 78},
                                                         'Discharge current': {'Current (A)': -0.005},
                                                         # cutoff is missing
                                                         'Discharge pulse': {'Duration': 600},
                                                         'Discharge relaxation': {'Duration': 600},
                                                         'OCP determination 3': {'Timeout': 30},
                                                         # FRA measurement settings
                                                         'Export ASCII data': {'Filename': r'C:\Users\LaborRatte_23_3\Documents\My Procedures 1.11\pitt.txt'}},
                                                     'plot': 'impedance',
                                                     'onoffafter': 'off',
                                                     'safepath': r"C:\Users\SDC_1\Documents\Github\helao-dev\temp",
                                                     'filename': 'eis.nox',
                                                     'parseinstructions': ['FIAMeasPotentiostatic']}

config['langDriver'] = dict(vx=5, vy=5, vz=5, port='COM3',
                            dll=r"C:\Users\LaborRatte23-2\Documents\git\pyLang\LStepAPI\_C#_VB.net\CClassLStep64",
                            dllconfig=r"C:\Users\LaborRatte23-2\Documents\git\pyLang\config.LSControl",
                            )

config['lang'] = dict(url="http://127.0.0.1:13382",
                      safe_home_pos=[0.0, 0.0, 0.0],
                        # 60.0, 70.0, -6.1348, #2.0, 85.0, 0.0
                        safe_waste_pos=[46.5, -108, 0], #3.0, -31.0, 0.0
                        safe_sample_pos=[-5.5, -89, 0], #3.0, 4.0, 0.0
                        remove_drop=[46.5, -94.0, 8.0], #3.0, -15.0, 10.25
                        forceurl="http://127.0.0.1:13379")

config['forceDriver'] = dict(port=5,buffer_size=1,
                             dll_address=r"C:\Users\LaborRatte23-2\Desktop\megsv\megsv_x64\MEGSV.dll")


#config['forceDriver'] = dict(com_port=8) 
config['force'] = dict(url="http://127.0.0.1:13378")

config['minipumpDriver'] = dict(port='COM4', baud=1200, timeout=1)
config['minipump'] = dict(url="http://127.0.0.1:13386") #127.0.0.1", port=13386
#
config['orchestrator'] = dict(path=r'C:\Users\LaborRatte23-2\Documents\data', kadiurl="http://127.0.0.1:13377")


config['launch'] = dict(server=['autolabDriver', 'kadiDriver', 'langDriver', 'minipumpDriver', 'forceDriver'], #, 'forceDriver'
                        action=['autolab', 'kadi', 'lang', 'minipump', 'force'], #, 'force'
                        orchestrator=['orchestrator'],
                        visualizer=['autolab_visualizer'],
                        process=[])

config['instrument'] = "sdc"

