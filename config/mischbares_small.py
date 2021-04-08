config = dict()

# we define all the servers here so that the overview is a bit better
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
                         minipumpingServer=dict(host="127.0.0.1", port=13390),
                         measureServer=dict(host="127.0.0.1", port=13368),
                         analysisServer=dict(host="127.0.0.1", port=13369),
                         learningServer=dict(host="127.0.0.1", port=13364))

config['kadi'] = dict(host=r"https://polis-kadi4mat.iam-cms.kit.edu",
                      PAT=r"78ac200f0379afb4873c7b0ee71f5489946158fe882466a9", group='2')

config['movement'] = dict(
    safe_sample_joints=[-56.0, 30.0, 40.0, 5.0, -72.0, 0.0],
    #pose (151.917, -245.409, 133.264, -42.574, -22.04, -70.12)
    safe_reservoir_joints=[-113.5733, 53.743, - \
                           1.5102, -132.2144, -65.2762, 32.6695],
    safe_waste_joints=[-10.0, -20.0, 45.0, 0.0, -25.0, 0.0],
    sample_rotation=0.0, reservoir_rotation=0.0, waste_rotation=0.0,
    x_limit_sample=75, y_limit_sample=75,
    x_limit_reservoir=75, y_limit_reservoir=75,
    x_limit_waste=10, y_limit_waste=10)

# Cofiguration of the pump
config['pump'] = dict(port='COM2', baud=9600, timeout=0.1,
                      pumpAddr={i: i + 21 for i in range(14)})  # numbering is left to right top to bottom
config['pump']['pumpAddr'].update({i: i for i in range(20, 35)})
config['pump']['pumpAddr']['all'] = 20

# Configuration of the potensiostat
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
                                       'ms': r'C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\config\echemprocedures\mott_schotky_no_osc.nox'})


# Configuration of the electrochemical experiments
config['echem'] = dict(procedures=dict())

config['echem']['procedures']['ca'] = {'procedure': 'ca',
                                       'setpoints': {'applypotential': {'Setpoint value': 0.735},
                                                     'recordsignal': {'Duration': 1000}},
                                       'plot': 'tCV',
                                       'onoffafter': 'off',
                                       'safepath': r"C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\temp",
                                       'filename': 'ca.nox',
                                       'parseinstructions': ['recordsignal']}


#{'Setpoint value': 0.01},{'Duration': 10}
# 'applypotential','recordsignal'
# C:\Users\Operator\Documents\auro-master\temp
# C:\Users\SDC_1\Documents\deploy\helao-dev\temp
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


# Configuration of the lang motor
config['lang'] = dict(vx=5, vy=5, vz=5, port='COM3',
                      dll=r"C:\Users\LaborRatte23-3\Documents\git\pyLang\LStepAPI\_C#_VB.net\CClassLStep64",
                      dllconfig=r"C:\Users\LaborRatte23-3\Documents\git\pyLang\config.LSControl",
                      safe_home_pos=[0.0, 0.0, 0.0],
                      # 60.0, 70.0, -6.1348, #2.0, 85.0, 0.0
                      safe_waste_pos=[30.0, 100.0, 0.0],
                      safe_sample_pos=[9.0, 10.0, 0.0],
                      remove_drop=[30.0, 75.0, 12.26])  # 1.3 #4.5 #30.0, 80.0, 9.75

# Configuration of the Arcoptix FTIR
#config['arcoptix'] = dict(dll = r'C:\Users\jkflowers\Desktop\arcoptix\API\Rocket_2_4_9_LabVIEWDrivers\200-LabVIEWDrivers\ARCsoft.ARCspectroMd')
config['arcoptix'] = dict(
    dll=r'..\..\..\arcoptix\API\Rocket_2_4_9_LabVIEWDrivers\200-LabVIEWDrivers\ARCsoft.ARCspectroMd')


# Configuration of the megsv force sensor
config['megsv'] = dict(port=5,
                       buffer_size=1,
                       dll_address=r"C:\Users\LaborRatte23-3\Desktop\megsv\megsv_x64\MEGSV.dll")

config['orchestrator'] = dict(
    path=r'C:\Users\Operator\Desktop\idk')

config['owis'] = dict(serials=[dict(port='COM4', baud=9600, timeout=0.1), dict(
    port='COM6', baud=9600, timeout=0.1)])

# Cofiguration of the mini pump
config['minipump'] = dict(port='COM2', baud=1200, timeout=1)
