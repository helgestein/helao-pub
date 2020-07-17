config = dict()

#we define all the servers here so that the overview is a bit better
config['servers'] = dict(pumpServer = dict(host="127.0.0.1", port=13370),
                         pumpingServer = dict(host="127.0.0.1", port=13371),
                         mecademicServer = dict(host="127.0.0.1", port=13372),
                         movementServer = dict(host="127.0.0.1", port=13373),
                         autolabServer = dict(host="127.0.0.1", port=13374),
                         echemServer = dict(host="127.0.0.1", port=13375),
                         kadiServer = dict(host="127.0.0.1", port=13376),
                         dataServer = dict(host="127.0.0.1", port=13377), 
                         megsvServer = dict(host="127.0.0.1", port= 13378),
                         sensingServer = dict(host="127.0.0.1", port= 13379),
                         orchestrator = dict(host= "127.0.0.1", port= 13380),
                         oceanServer = dict(host= "127.0.0.1", port= 13381),
                         smallRamanServer = dict(host= "127.0.0.1", port= 13382))

config['kadi'] = dict(host = r"https://kadi4mat.iam-cms.kit.edu",
            PAT = r"98d7dfbcd77a9163dde2e8ca34867a4998ecf68bc742cf4e")

config['movement'] = dict(
    safe_sample_joints = [-56.0, 30.0, 40.0, 5.0, -72.0, 0.0],
    #pose (151.917, -245.409, 133.264, -42.574, -22.04, -70.12)
    safe_reservoir_joints = [-113.5733, 53.743, -1.5102, -132.2144, -65.2762, 32.6695],
    safe_waste_joints = [-10.0, -20.0, 45.0, 0.0, -25.0, 0.0],
    sample_rotation = 0.0, reservoir_rotation = 0.0, waste_rotation = 0.0,
    x_limit_sample = 75, y_limit_sample = 75,
    x_limit_reservoir = 75, y_limit_reservoir = 75,
    x_limit_waste = 10, y_limit_waste = 10)

## Cofiguration of the pump
config['pump'] = dict()

## Configuration of the potensiostat
config['autolab'] = dict(basep = r"C:\Program Files\Metrohm Autolab\Autolab SDK 1.11",
                    procp = r"C:\Users\Operator\Documents\GitHub\hans\config\echemprocedures\echemprocedures",
                    #hwsetupf = r"C:\ProgramData\Metrohm Autolab\12.0\HardwareSetup.AUT88172.xml",
                    hwsetupf = r"C:\ProgramData\Metrohm Autolab\12.0\HardwareSetup.AUT88007.xml",
                    micsetupf = r"C:\Program Files\Metrohm Autolab\Autolab SDK 1.11\Hardware Setup Files\Adk.bin",
                    proceuduresd = {'cp': r'C:\Users\Operator\Documents\GitHub\hans\config\echemprocedures\CP.nox',
                                    'ca': r'C:\Users\Operator\Documents\GitHub\hans\config\echemprocedures\CA.nox',
                                    'cv': r'C:\Users\Operator\Documents\GitHub\hans\config\echemprocedures\CV.nox',
                                    'eis': r'C:\Users\Operator\Documents\GitHub\hans\config\echemprocedures\EIS.nox',
                                    'ocp': r'C:\Users\Operator\Documents\GitHub\hans\config\echemprocedures\OCP.nox',
                                    'on': r'C:\Users\Operator\Documents\GitHub\hans\config\echemprocedures\ON.nox',
                                    'off': r'C:\Users\Operator\Documents\GitHub\hans\config\echemprocedures\OFF.nox'})

## Configuration of the electrochemical experiments
config['echem'] = dict(procedures=dict())

config['echem']['procedures']['ca'] = {'procedure': 'ca',
           'setpoints': {'applypotential': {'Setpoint value': 0.01},
                         'recordsignal': {'Duration': 10}},
           'plot': 'tCV',
           'onoffafter': 'off',
           'safepath': r"C:\Users\Operator\Documents\git\auro-master\temp",
           'filename': 'ca.nox',
           'parseinstructions': ['recordsignal']}

config['echem']['procedures']['cp'] = {'procedure': 'cp',
           'setpoints': {'applycurrent': {'Setpoint value': 10**-4},
                         'recordsignal': {'Duration': 10}},
           'plot': 'tCV',
           'onoffafter': 'off',
           'safepath': r"C:\Users\Operator\Documents\git\auro-master\temp",
           'filename': 'cp.nox',
           'parseinstructions': ['recordsignal']}

config['echem']['procedures']['cv'] = {'procedure': 'cv',
           'setpoints': {
               'FHSetSetpointPotential': {'Setpoint value':0},
               'FHWait': {'Time':2},
               'CVLinearScanAdc164': {'StartValue': 0.0,
                                      'UpperVertex': 0.5,
                                      'LowerVertex': -0.5,
                                      'NumberOfStopCrossings': 2,
                                      'ScanRate': 0.1}},
           'plot': 'tCV',
           'onoffafter': 'off',
           'safepath': r"C:\Users\Operator\Documents\git\auro-master\temp",
           'filename': 'cv.nox',
           'parseinstructions': ['CVLinearScanAdc164']}

config['echem']['procedures']['eis'] = {'procedure': 'eis',
            'setpoints': {'FHSetSetpointPotential': {'Setpoint value': 0.01}},
            'plot': 'impedance',
            'onoffafter': 'off',
            'safepath': r"C:\Users\Operator\Documents\git\auro-master\temp",
            'filename': 'eis.nox',
            'parseinstructions': ['FIAMeasPotentiostatic']}

config['megsv'] = dict(port = 4, 
                        buffer_size= 1000,
                        dll_address= r"..\dll\MEGSV.dll")

