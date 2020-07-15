import requests
import time
import sys 
sys.path.append(r'.../action')
sys.path.append(r'.../server')
sys.path.append(r'.../config')
from mischbares_small import config
from fastapi import FastAPI
from pydantic import BaseModel
import json
import requests

# In order to run the orchatrator which is at the highest level of Helao, all servers should be started. 

#Action book 
# still motor functions need to be added. 
sdc_std = ['movement/matrixRotation','movement/moveToHome','movement/jogging','movement/alignSample', 'movement/alignReservoir', 
           'movement/alignWaste', 'movement/alignment','movement/mvToSample', 'movement/mvToReservoir', 'movement/mvToWaste', 
           'movement/moveUp', 'movement/removeDrop', 'pumping/formulation_succ','pumping/formulation', 'pumping/flushSerial',
           'echem/measure','echem/ismeasuring', 'echem/potential', 'echem/current', 'echem/setcurrentrange', 'echem/appliedpotential', 
           'echem/cellonoff', 'echem/retrieve', 'forceAction/read', 'data/addrecord', 'data/addcollection'] 


#this orchestrator manages a list of experiments and expects 
#dispense a formulation
pumpurl = "http://{}:{}".format("127.0.0.1", "13370")
res = requests.get("{}/pumping/formulation".format(pumpurl), 
                    params={comprel: [0.2,0.2,0.2,0.2,0.2], pumps: [0,1,2,3,4], speed: 1000, totalvol: 1000}).json()


experiment_list = []
#this is a highly complex experiment spec
experiment_spec = dict(
                       soe=['movement/home','movement/waste','pumpingDispense_0','movement/drop',
                            'movement/home','movement/sample','echem/measure','pump/aspirate',
                            'movement/home','movement/waste','pumping/dispense_2','movement/drop',
                            'movement/home','movement/sample','echem/measure_2','pump/aspirate_2',
                            'analyze/maxcurr','plan/al','data/save'],
  # in params , you should give the input values.
                       params = dict('home':None,
                                     'waste':dict(position={'x':0,'y':0}),
                                     'dispense':dict(formulation=[0.2,0.2,0.2,0.2,0.2],
                                                     pumps=[0,1,2,3,4],
                                                     speed=1000,
                                                     direction=1,
                                                     stage=True,totalVol=2000])),
                                     'dispense_2':dict(formulation=[1],
                                                     pumps=[5],
                                                     speed=4000,
                                                     direction=1,
                                                     stage=True,totalVol=2000])),
                                     'drop':dict('delta_x':20),
                                     'measure':dict('procedure'='ca',
                                                    'setpoints'=dict('applypotential' = {'Setpoint value': -0.5},
                                                                     'recordsignal' = {'Duration': 300}),
                                                    'plot':False,
                                                    'onoffafter':'off'),
                                     'measure_2':dict('procedure'='ca',
                                                      'setpoints'=dict('FHSetSetpointPotential': {'Setpoint value':0},
                                                      'FHWait': {'Time':2},
                                                      'CVLinearScanAdc164': {'StartValue': 0.0,
                                                                            'UpperVertex': 1.5,
                                                                            'LowerVertex': -0.25,
                                                                            'NumberOfStopCrossings': 2,
                                                                            'ScanRate': 0.02}),
                                                    'plot':False,
                                                    'onoffafter':'off'),
                                     'aspirate':dict('amount'=1000),
                                     'aspirate_2':dict('amount'=100),
                                     'maxcurr':dict(pot=1.5,ref='OER'),
                                     'al':dict(inputs=dict(dispense='formulation')))

while True:
    if experiment_list == []:
        print('nothing to do. Sleeping for a second')
        time.sleep(1)
    else:
        #now we do something from the list
        current_experiment = experiment_list.pop(0)
        #select the actions to do and excecute them from the _s_equence _o_f _e_vents
        for actionSelect in current_experiment['soe']:
            server,action = actionSelect.split('/')
             

