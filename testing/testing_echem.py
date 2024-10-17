import requests
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
import time
import json
from config.mischbares_small import config
from config.sdc_4 import config

def echem_test(action, params):
    server = 'autolab'
    action = action
    params = params
    res = requests.get("http://{}:{}/{}/{}".format(
        config['servers']['autolab']['host'], 
        config['servers']['autolab']['port'],server , action),
        params= params).json()
    return res

# test all the actions    
echem_test('potential', None)
echem_test('ismeasuring', None)
echem_test('current', None)
echem_test('appliedpotential', None)
echem_test('setcurrentrange', params=dict(crange='10uA'))
echem_test('cellonoff', dict(onoff='off'))

echem_test('measure', params=dict(procedure="ca", setpointjson="{'applypotential': {'Setpoint value': 0.01}, 'recordsignal': {'Duration': 20}}", plot="tCV", onoffafter="off", safepath="C:/Users/LaborRatte23-3/Documents/GitHub/helao-dev/temp", filename="ca.nox", parseinstructions="recordsignal"))


echem_test('measure', params=dict(procedure="cv", setpointjson= json.dumps({'FHSetSetpointPotential': {'Setpoint value': -1}, 'FHWait': {'Time': 10}, 'CVLinearScanAdc164': {'StartValue': -1, 'UpperVertex': -0.5, 'LowerVertex':-1.5, 'NumberOfStopCrossings': 6, 'ScanRate': 0.1}}),plot="tCV",onoffafter="off", safepath="C:/Users/LaborRatte23-3/Documents/GitHub/helao-dev/temp", filename="cv.nox",parseinstructions='CVLinearScanAdc164'))

# echem_test('measure', params=dict(procedure="cv", setpointjson= json.dumps({'FHSetSetpointPotential': {'Setpoint value': -0.145}, 'FHWait': {'Time': 10},
#                              'CVLinearScanAdc164': {'StartValue': -0.145, 'UpperVertex': 0.4, 'LowerVertex':-0.3, 'NumberOfStopCrossings': 2, 'Step': 0.004, 'ScanRate': 0.02}}),
#                              plot="tCV",
#                              onoffafter="off",
#                              safepath="C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp", 
#                              filename="test_cv.nox",
#                              parseinstructions='CVLinearScanAdc164'))

echem_test('measure', params=dict(procedure="cv", setpointjson= json.dumps({'FHSetSetpointPotential': {'Setpoint value': -0.145}, 'FHWait': {'Time': 10},
                             'CVLinearScanAdc164': {'StartValue': -0.145, 'UpperVertex': 0.4, 'LowerVertex':-0.3, 'NumberOfStopCrossings': 2, 'StepValue': 0.004, 'ScanRate': 0.020}}),
                             plot="tCV",
                             onoffafter="off",
                             safepath="C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp", 
                             filename="test_cv.nox",
                             parseinstructions='CVLinearScanAdc164'))

echem_test('measure', params=dict(procedure="cv_ocp", setpointjson= json.dumps({'FHRefDetermination': {'Timeout': 30},
                                'FHWait': {'Time': 5},
                                'FHCyclicVoltammetry2': {'Upper vertex': 0.75,
                                                         'Lower vertex': -0.50,
                                                         'Step': 0.004,
                                                         'NrOfStopCrossings': 2,
                                                         'Scanrate': 0.020}}),
                             plot="tCV",
                             onoffafter="off",
                             safepath="C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp", 
                             filename="cv_ocp_test.nox",
                             parseinstructions='FHCyclicVoltammetry2'))


echem_test('measure', params=dict(procedure="cv_fc", setpointjson= json.dumps({'FHSetSetpointPotential': {'Setpoint value': -0.100}, 'FHWait': {'Time': 10},
                             'FHCyclicVoltammetry2': {'Start value': -0.100, 'Upper vertex': 0.600, 'Lower vertex':-0.400, 'NrOfStopCrossings': 2, 'Step': 0.004, 'Scanrate': 0.020}}),
                             plot="tCV",
                             onoffafter="off",
                             safepath="C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp", 
                             filename="cv_fc_test.nox",
                             parseinstructions='FHCyclicVoltammetry2'))

echem_test('measure', params=dict(procedure="cp", setpointjson= json.dumps({'applycurrent0': {'Setpoint value': 10**-8},'applycurrent': {'Setpoint value': 10**-8}, 'recordsignal': {'Duration': 2}}),
                                plot="tCV",
                                onoffafter="off",
                                safepath="C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                filename="cp.nox",
                                parseinstructions='recordsignal'))

echem_test('measure', params=dict(procedure="charge", setpointjson= json.dumps({'applycurrent': {'Setpoint value': 10**-8}, 'recordsignal': {'Duration': 3}}),
                                plot="tCV",
                                onoffafter="off",
                                safepath="C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                filename="Chronopotentiometry charge protocol.nox",
                                parseinstructions='recordsignal'))                                

echem_test('measure', params=dict(procedure="gcpl_fc", setpointjson= json.dumps({'applycurrent0': {'Setpoint value': 2e-7},'applycurrent': {'Setpoint value': 2e-7}, 'recordsignal': {'Duration': 60, 'Interval time in µs': 0.5}}),
                                plot="tCV",
                                onoffafter="off",
                                safepath="C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                filename="gcpl_fc.nox",
                                parseinstructions='recordsignal'))

echem_test('measure', params=dict(procedure="gdpl_fc", setpointjson= json.dumps({'applycurrent0': {'Setpoint value': -2e-7},'applycurrent': {'Setpoint value': -2e-7}, 'recordsignal': {'Duration': 60, 'Interval time in µs': 0.5}}),
                                plot="tCV",
                                onoffafter="off",
                                safepath="C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                filename="gcpl_fc.nox",
                                parseinstructions='recordsignal'))

echem_test('measure', params=dict(procedure="ocp_rs", setpointjson= json.dumps({'recordsignal': {'Duration': 20, 'Interval time in µs': 1}}),
                                plot="tCV",
                                onoffafter="off",
                                safepath="C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp",
                                filename="ocp_rs_test.nox",
                                parseinstructions='recordsignal'))



echem_test('measure', params=dict(procedure="ms", setpointjson= json.dumps({'FHSetSetpointPotential': {'Setpoint value': 0.01}}),
                        plot="impedance",
                        onoffafter="off",
                        safepath= r"C:\Users\LaborRatte23-3\Documents\GitHub\helao-dev\temp",
                        filename="ms.nox",
                        parseinstructions= ['FHLevel', 'FIAMeasurement']))   #["FIAMeasurement", "FHLevel"]

echem_test('measure', params=dict(procedure="eis_ocp", setpointjson=json.dumps({'FHRefDetermination': {'Timeout': 120}}),
            plot="impedance",
            onoffafter="off",
            safepath= r"C:\Users\LaborRatte23-2\Documents\GitHub\helao-dev_2\temp",
            filename="eis_ocp_test.nox",
            parseinstructions= ['FIAMeasPotentiostatic']))
 
echem_test('measure', params=dict(procedure="eis", setpointjson=json.dumps({'FHSetSetpointPotential': {'Setpoint value': 3.07}}),
            plot="impedance",
            onoffafter="off",
            safepath= r"C:\Users\LaborRatte23-2\Documents\GitHub\helao-dev_2\temp",
            filename="eis_test.nox",
            parseinstructions= ['FIAMeasPotentiostatic']))
            
echem_test('measure', params=dict(procedure="eis_fast", setpointjson=json.dumps({'FHSetSetpointPotential': {'Setpoint value': 0.00}}),
            plot="impedance",
            onoffafter="off",
            safepath= r"C:\Users\LaborRatte23-2\Documents\GitHub\helao-dev_2\temp",
            filename="eis_test_Cu_tape.nox",
            parseinstructions= ['FIAMeasPotentiostatic']))
            

echem_test('measure', params=dict(procedure= 'ocp', setpointjson= "{'FHLevel' : {'Duration': 120}}", plot= 'tCV', onoffafter='off', safepath= "C:\Users\LaborRatte23-3\Documents\helao-dev\temp",filename= 'ocp.nox', parseinstructions= ['FHLevel']))


echem_test('measure', params=dict(procedure= 'ocp_rf', setpointjson= "{'FHRefDetermination' : {'Timeout': 20}}", plot= 'tCV', onoffafter='off', safepath= "C:\Users\LaborRatte23-3\Documents\helao-dev\temp",filename= 'ocp_rf.nox', parseinstructions= ['OCP determination']))

echem_test('measure', params=dict(procedure= 'ocp_rf', setpointjson= "{'FHRefDetermination' : {'Timeout': 20}}", plot= 'tCV', onoffafter='off', safepath= "C:\Users\LaborRatte23-2\Documents\GitHub\helao-dev_2\temp",filename= 'ocp_rf.nox', parseinstructions= ['OCP determination']))