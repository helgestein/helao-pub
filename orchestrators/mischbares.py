# In order to run the orchatrator which is at the highest level of Helao, all servers should be started. 
import requests
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
import time
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
           'echem/cellonoff', 'echem/retrieve', 'forceAction/read',  'data/addrecord', 'data/addcollection' ] 



#This is a highly complex experiment spec
  # in params , you should give the input values.
  # 'forceAction/read_0','data/addrecord_0'
experiment_spec = dict(
                       soe=['movement/moveToHome_0','movement/alignment_0','movement/mvToWaste_0','pumping/formulation_0',
                            'movement/removeDrop_0','movement/moveToHome_1','movement/mvToSample_0',
                            'echem/measure_0','pump/formulation_1','movement/moveToHome_2','movement/mvToWaste_1',
                            'pumping/formulation_2','movement/removeDrop_1','movement/moveToHome_4','movement/mvToSample_1',
                            'echem/measure_1','pump/formulation_3'], 

                       params = dict(moveToHome_0 = None,
                                     alignment_0 = None,
                                     mvToWaste_0 = dict(x= 0.0,y= 0.0),
                                     formulation_0 = dict(formulation= [0.2,0.2,0.2,0.2,0.2],
                                                     pumps= [0,1,2,3,4],
                                                     speed= 1000,
                                                     direction= -1,
                                                     stage= True,
                                                     totalVol= 2000),
                                     removeDrop_0 = dict(y= -20),
                                     moveToHome_1 = None,
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
                                    moveToHome_2 = None,
                                    mvToWaste_1 = dict(position= {'x':0.0,'y':0.0}),
                                    fomulation_2 = dict(formulation= [1],
                                                     pumps= [5],
                                                     speed= 4000,
                                                     direction= -1,
                                                     stage= True,
                                                     totalVol= 2000), 
                                    removeDrop_1 = dict(y = -20), 
                                    moveToHome_3 = None,
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
                                    ))

#addrecord_0= dict(ident= 1,title= 'electrodeposition', filed= 'cu-No3', visibility='private',meta=None)
        
experiment = json.dumps(experiment_spec)

#### writing the orchastrator server
app = FastAPI(title = "orchestrator", description = "A fancy complex server",version = 1.0)

def addToQueue(experiment: str):
    dict_input = json.loads(experiment)
    experiment_list.append(dict_input)
    return experiment_list


@app.get("/orchestrator/runAll")
def execute(experiment: str):
    experiment_list = addToQueue(experiment)
    for action_str in experiment_list[0]['soe']:

        server, fnc = action_str.split('/') #Beispiel: action: 'movement' und fnc : 'moveToHome_0
        action = fnc.split('_')[0]

        if server == 'movement':
            requests.get("https//{}:{}/{}/{}".format(config['servers']['movementServer']['host'], config['servers']['movementServer']['port'],server , action),
                        params= experiment_list[0]['params'][fnc]).json
        elif server == 'pumping':
            requests.get("http://{}:{}/{}/{}".format(config['servers']['pumpingServer']['host'], config['servers']['pumpingServer']['port'],server, action),
                        params= experiment_list[0]['params'][fnc]).json
        elif server == 'echem':
            requests.get("http://{}:{}/{}/{}".format(config['servers']['echemServer']['host'], config['servers']['echemServer']['port'],server, action),
                        params= experiment_list[0]['params'][fnc]).json
        elif server == 'forceAction':
            requests.get("http://{}:{}/{}/{}".format(config['servers']['sensingServer']['host'], config['servers']['sensingServer']['port'],server, action),
                        params= experiment_list[0]['params'][fnc]).json
        elif server == 'data':
            requests.get("http://{}:{}/{}/{}".format(config['servers']['dataServer']['host'], config['servers']['dataServer']['port'],server, action),
                        params= experiment_list[0]['params'][fnc]).json
        
if __name__ == "__main__":
    uvicorn.run(app, host= config['servers']['orchestrator']['host'], port= config['servers']['orchestrator']['port'])
    print("orchestrator is instantiated. ")
    experiment_list = []
    while True:
        if experiment_list == []:
            time.sleep(1)
            print('There is nothing to do')

        elif len(experiment_list) > 0:
            execute(experiment_list)

# We do not need the pop(0), because  we are iterating through a for loop

