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
                         motorServer = dict(host= "127.0.0.1", port= 13381),
                         langServer = dict(host= "127.0.0.1", port= 13382),
                         oceanServer = dict(host= "127.0.0.1", port= 13383),
                         smallRamanServer = dict(host= "127.0.0.1", port= 13384),
                         arcoptixServer = dict(host= "127.0.0.1", port= 13385),
                         ftirServer = dict(host= "127.0.0.1", port= 13386),
                         owisServer = dict(host= "127.0.0.1", port= 13387),
                         tableServer = dict(host= "127.0.0.1", port= 13388))

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
config['pump'] = dict(port='COM2', baud=9600, timeout=0.1,
                      pumpAddr={i: i + 21 for i in range(14)} ) # numbering is left to right top to bottom
config['pump']['pumpAddr'].update({i:i for i in range(20,35)})
config['pump']['pumpAddr']['all'] = 20

## Configuration of the potensiostat
config['autolab'] = dict(basep = r"C:\Program Files\Metrohm Autolab\Autolab SDK 1.11",
                    procp = r"C:\Users\SDC_1\Documents\deploy\helao-dev\config\echemprocedures\echemprocedures",
                    #hwsetupf = r"C:\ProgramData\Metrohm Autolab\12.0\HardwareSetup.AUT88172.xml",
                    hwsetupf = r"C:\ProgramData\Metrohm Autolab\12.0\HardwareSetup.AUT88007.xml",
                    micsetupf = r"C:\Program Files\Metrohm Autolab\Autolab SDK 1.11\Hardware Setup Files\Adk.bin",
                    proceuduresd = {'cp': r'C:\Users\SDC_1\Documents\deploy\helao-dev\config\echemprocedures\CP.nox',      
                                    'ca': r'C:\Users\SDC_1\Documents\deploy\helao-dev\config\echemprocedures\CA.nox',
                                    'cv': r'C:\Users\SDC_1\Documents\deploy\helao-dev\config\echemprocedures\CV.nox',
                                    'eis': r'C:\Users\SDC_1\Documents\deploy\helao-dev\config\echemprocedures\EIS.nox',
                                    'ocp': r'C:\Users\SDC_1\Documents\deploy\helao-dev\config\echemprocedures\OCP.nox',
                                    'on': r'C:\Users\SDC_1\Documents\deploy\helao-dev\config\echemprocedures\ON.nox',
                                    'off': r'C:\Users\SDC_1\Documents\deploy\helao-dev\config\echemprocedures\OFF.nox'})

## Configuration of the electrochemical experiments
config['echem'] = dict(procedures=dict())

config['echem']['procedures']['ca'] = {'procedure': 'ca',
           'setpoints': {'applypotential': {'Setpoint value': 0.01},
                         'recordsignal': {'Duration': 10}},
           'plot': 'tCV',
           'onoffafter': 'off',
           'safepath': r"C:\Users\SDC_1\Documents\deploy\helao-dev\temp",
           'filename': 'ca.nox',
           'parseinstructions': ['recordsignal']}


#{'Setpoint value': 0.01},{'Duration': 10}
#'applypotential','recordsignal'
# C:\Users\Operator\Documents\auro-master\temp
# C:\Users\SDC_1\Documents\deploy\helao-dev\temp


config['echem']['procedures']['cp'] = {'procedure': 'cp',
           'setpoints': {'applycurrent': {'Setpoint value': 10**-4},
                         'recordsignal': {'Duration': 10}},
           'plot': 'tCV',
           'onoffafter': 'off',
           'safepath': r"C:\Users\SDC_1\Documents\deploy\helao-dev\temp",
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
           'safepath': r"C:\Users\SDC_1\Documents\deploy\helao-dev\temp",
           'filename': 'cv.nox',
           'parseinstructions': ['CVLinearScanAdc164']}

config['echem']['procedures']['eis'] = {'procedure': 'eis',
            'setpoints': {'FHSetSetpointPotential': {'Setpoint value': 0.01}},
            'plot': 'impedance',
            'onoffafter': 'off',
            'safepath': r"C:\Users\SDC_1\Documents\deploy\helao-dev\temp",
            'filename': 'eis.nox',
            'parseinstructions': ['FIAMeasPotentiostatic']}


#Configuration of the lang motor
config['lang'] = dict(vx = 5, vy = 5, vz = 5, port = 'COM4', 
                      dll = r"C:\Users\SDC_1\Documents\git\pyLang\LStepAPI\_C#_VB.net\CClassLStep64",
                      dllconfig = r"C:\Users\SDC_1\Documents\git\pyLang\config.LSControl", 
                      safe_home_pos = [2.0, 35.0, 0.0], 
                      safe_waste_pos = [40.0, 85.0, 0.0], # 60.0, 70.0, -6.1348, #2.0, 85.0, 0.0
                      safe_sample_pos = [73.0, 42.0, 13.0], 
                      remove_drop= [53.5, 90.0, 7.5])

#Configuration of the Arcoptix FTIR
#config['arcoptix'] = dict(dll = r'C:\Users\jkflowers\Desktop\arcoptix\API\Rocket_2_4_9_LabVIEWDrivers\200-LabVIEWDrivers\ARCsoft.ARCspectroMd')
config['arcoptix'] = dict(dll = r'..\..\..\arcoptix\API\Rocket_2_4_9_LabVIEWDrivers\200-LabVIEWDrivers\ARCsoft.ARCspectroMd')


#Configuration of the megsv force sensor
config['megsv'] = dict(port = 5, 
                        buffer_size= 1,
                        dll_address= r"C:\Users\SDC_1\Desktop\megsv\megsv_x64\MEGSV.dll")

config['orchestrator'] = dict(path=r'C:\Users\SDC_1\Documents\data')

config['owis'] = dict(serials=[dict(port='COM4', baud=9600, timeout=0.1),dict(port='COM6', baud=9600, timeout=0.1)])