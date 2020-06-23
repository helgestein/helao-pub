import requests


#dispense a formulation
pumpurl = "http://{}:{}".format("127.0.0.1", "13370")
res = requests.get("{}/pumping/formulation".format(pumpurl), 
                    params={comprel: [0.2,0.2,0.2,0.2,0.2], pumps: [0,1,2,3,4], speed: 1000, totalvol: 1000}).json()


import requests
import time
#start all servers if not already done

#this orchestrator manages a list of experiments and expects 
#dispense a formulation
pumpurl = "http://{}:{}".format("127.0.0.1", "13370")
res = requests.get("{}/pumping/formulation".format(pumpurl), 
                    params={comprel: [0.2,0.2,0.2,0.2,0.2], pumps: [0,1,2,3,4], speed: 1000, totalvol: 1000}).json()


experiment_list = []
#this is a highly complex experiment spec
experiment_spec = dict(position = dict(x=3,y=5,force=3),
                       soe=['movement/home','movement/waste','pumping/dispense','movement/drop',
                            'movement/home','movement/sample','echem/measure','pump/aspirate',
                            'movement/home','movement/waste','pumping/dispense_2','movement/drop',
                            'movement/home','movement/sample','echem/measure_2','pump/aspirate_2',
                            'analyze/maxcurr','plan/al','data/save'],
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
             

