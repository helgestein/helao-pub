# In order to run the orchatrator which is at the highest level of Helao, all servers should be started. 
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
import uvicorn
from typing import List
from fastapi import FastAPI, Query
import json

#Action book 
# still motor functions need to be added. 
sdc_std = ['movement/matrixRotation','movement/moveToHome','movement/jogging','movement/alignSample', 'movement/alignReservoir', 
           'movement/alignWaste', 'movement/alignment','movement/mvToSample', 'movement/mvToReservoir', 'movement/mvToWaste', 
           'movement/moveUp', 'movement/removeDrop', 'pumping/formulation_succ','pumping/formulation', 'pumping/flushSerial',
           'echem/measure','echem/ismeasuring', 'echem/potential', 'echem/current', 'echem/setcurrentrange', 'echem/appliedpotential', 
           'echem/cellonoff', 'echem/retrieve', 'forceAction/read', 'data/addrecord', 'data/addcollection'] 



#This is a highly complex experiment spec
  # in params , you should give the input values.
experiment_spec = dict(
                       soe=['movement/moveToHome_0','movement/alignment_0','movement/mvToWaste_0','pumping/formulation_0',
                            'movement/removeDrop_0','movement/moveToHome_1','movement/mvToSample_0','forceAction/read_0',
                            'echem/measure_0','pump/formulation_1','movement/moveToHome_2','movement/mvToWaste_1',
                            'pumping/formulation_2','movement/removeDrop_1','movement/moveToHome_4','movement/mvToSample_1',
                            'echem/measure_1','pump/formulation_3','data/addrecord_0'], 

                       params = dict(moveToHome_0 = None,
                                     mvToWaste_0 = dict(position={'x':0.0,'y':0.0}),
                                     formulation_0 = dict(formulation= [0.2,0.2,0.2,0.2,0.2],
                                                     pumps= [0,1,2,3,4],
                                                     speed= 1000,
                                                     direction= -1,
                                                     stage= True,
                                                     totalVol= 2000),
                                     removeDrop_0 = dict(y= (-20)),
                                     mvToSample_0 = dict(x= 20, y= 10),
                                     measure_0= dict(procedure= 'ca',
                                                    setpoints= dict(applypotential = {'Setpoint value': -0.5},
                                                                     recordsignal= {'Duration': 300}),
                                                    plot= False,
                                                    onoffafter= 'off'),
                                     fomulation_1 = dict(formulation=[1],
                                                     pumps=[5],
                                                     speed=4000,
                                                     direction=1,
                                                     stage=True,
                                                     totalVol=2000),
                                    mvToWaste_1 = dict(position= {'x':0.0,'y':0.0}),
                                    fomulation_2 = dict(formulation= [1],
                                                     pumps= [5],
                                                     speed= 4000,
                                                     direction= -1,
                                                     stage= True,
                                                     totalVol= 2000), 
                                    removeDrop_1 = dict(y = -20), 
                                    mvToSample_1 = dict(x= 18, y= 8), 
                                    measure_1= dict(procedure= 'ca',
                                                    setpoints= dict(applypotential = {'Setpoint value': -0.5},
                                                                     recordsignal= {'Duration': 300}),
                                                    plot= False,
                                                    onoffafter= 'off'),
                                    fomulation_3 = dict(formulation=[1],
                                                     pumps=[5],
                                                     speed=4000,
                                                     direction=1,
                                                     stage=True,
                                                     totalVol=2000),
                                    addrecord_0= dict(ident= 1,title= 'electrodeposition', filed= 'cu-No3',
                                                      visibility='private',meta=None))


        
experiment = json.dumps(experiment_spec)

#### writing the orchastrator server
app = FastAPI(title = "orchastrator", description = "A fancy complex server",version = 1.0)

def addToQueue(experiment: str):
    dict_input = json.load(experiment)
    experiment_list.append(dict_input)
    return experiment_list


@app.get("/orchastrator/runAll")
def execute(experiment_list: str):
    for action_str in experiment_list[0]['soe']:
        action, fnc = action_str.split('/') #Beispiel: action: 'movement' und fnc : 'moveToHome_0
        if action == 'movement':
            requests.get("/{}:{}/{}/{}".format(config['servers']['movementServer']['host'], config['servers']['movementServer']['port'],action, fnc),
                        params=fnc.split('_')[0]).json
        elif action == 'pumping':
            requests.get("/{}:{}/{}/{}".format(config['servers']['pumpingServer']['host'], config['servers']['pumpingServer']['port'],action, fnc),
                        params=fnc.split('_')[0]).json
        elif action == 'echem':
            requests.get("/{}:{}/{}/{}".format(config['servers']['echemServer']['host'], config['servers']['echemServer']['port'],action, fnc),
                        params=fnc.split('_')[0]).json
        elif action == 'forceAction':
            requests.get("/{}:{}/{}/{}".format(config['servers']['sensingServer']['host'], config['servers']['sensingServer']['port'],action, fnc),
                        params=fnc.split('_')[0]).json
        elif action == 'data':
            requests.get("/{}:{}/{}/{}".format(config['servers']['dataServer']['host'], config['servers']['dataServer']['port'],action, fnc),
                        params=fnc.split('_')[0]).json
        
if __name__ == "__main__":
    url = "http://{}:{}".format(config['servers']['orchestrator']['host'], config['servers']['orchestrator']['port']

    main()
    ":
    exp_list = []
    app 
    
    while True:
        if len(exp_list)>0:
            execute()



experiment_list = []


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
             

