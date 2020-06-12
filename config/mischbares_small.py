config = dict()
config['movement'] = dict(
    safe_sample_joints = [-56.0, 30.0, 40.0, 5.0, -72.0, 0.0],
    #pose (151.917, -245.409, 133.264, -42.574, -22.04, -70.12)
    safe_reservoir_joints = [-113.5733, 53.743, -1.5102, -132.2144, -65.2762, 32.6695],
    safe_waste_joints = [-10.0, -20.0, 45.0, 0.0, -25.0, 0.0],
    sample_rotation = 0, reservoir_rotation = 0, waste_rotation = 0,
    x_limit_sample = 75, y_limit_sample = 75,
    x_limit_reservoir = 75, y_limit_reservoir = 75,
    x_limit_waste = 10, y_limit_waste = 10)

## Cofiguration of the pump
config['pump'] = dict(direction_pin_B = 'd:13:o',
                      speed_pin_B = 'd:11:p',
                      brake_pin_B = 'd:8:o',
                      direction_pin_A = 'd:12:o',
                      speed_pin_A = 'd:3:p',
                      brake_pin_A = 'd:9:o',
                      radiusMotor = 0.2,
                      radiusTube = 0.02)

## Configuration of the potensiostat
config['autolab'] = dict(basep = "C:\Program Files\Metrohm Autolab\Autolab SDK 1.11",
                    procp = "C:\Users\Operator\Documents\GitHub\hans\config\echemprocedures\echemprocedures",
                    #hwsetupf = r"C:\ProgramData\Metrohm Autolab\12.0\HardwareSetup.AUT88172.xml",
                    hwsetupf = "C:\ProgramData\Metrohm Autolab\12.0\HardwareSetup.AUT88078.xml",
                    micsetupf = "C:\Program Files\Metrohm Autolab\Autolab SDK 1.11\Hardware Setup Files\Adk.bin",
                    proceuduresd = {'cp': 'C:\Users\Operator\Documents\GitHub\hans\config\echemprocedures\CP.nox',
                                    'ca': 'C:\Users\Operator\Documents\GitHub\hans\config\echemprocedures\CA.nox',
                                    'cv': 'C:\Users\Operator\Documents\GitHub\hans\config\echemprocedures\CV.nox',
                                    'eis': 'C:\Users\Operator\Documents\GitHub\hans\config\echemprocedures\EIS.nox',
                                    'ocp': 'C:\Users\Operator\Documents\GitHub\hans\config\echemprocedures\OCP.nox',
                                    'on': 'C:\Users\Operator\Documents\GitHub\hans\config\echemprocedures\ON.nox',
                                    'off': 'C:\Users\Operator\Documents\GitHub\hans\config\echemprocedures\OFF.nox'})

## Configuration of the electrochemical experiments
config['echem'] = dict(procedures=dict())

config['echem']['procedures']['ca'] = {'procedure': 'ca',
           'setpoints': {'applypotential': {'Setpoint value': 0.01},
                         'recordsignal': {'Duration': 10}},
           'plot': 'tCV',
           'onoffafter': 'off',
           'safepath': 'C:\Users\Operator\Documents\git\auro-master\temp',
           'filename': 'ca.nox',
           'parseinstructions': ['recordsignal']}

config['echem']['procedures']['cp'] = {'procedure': 'cp',
           'setpoints': {'applycurrent': {'Setpoint value': 10**-4},
                         'recordsignal': {'Duration': 10}},
           'plot': 'tCV',
           'onoffafter': 'off',
           'safepath': 'C:\Users\Operator\Documents\git\auro-master\temp',
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
           'safepath': 'C:\Users\Operator\Documents\git\auro-master\temp',
           'filename': 'cv.nox',
           'parseinstructions': ['CVLinearScanAdc164']}

config['echem']['procedures']['eis'] = {'procedure': 'eis',
            'setpoints': {'FHSetSetpointPotential': {'Setpoint value': 0.01}},
            'plot': 'impedance',
            'onoffafter': 'off',
            'safepath': "C:\Users\Operator\Documents\git\auro-master\temp",
            'filename': 'eis.nox',
            'parseinstructions': ['FIAMeasPotentiostatic']}
