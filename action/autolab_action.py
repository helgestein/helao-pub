""" A action server for electrochemistry

the logic here is that you define recipes that are stored in files. This is a relatively specific implementation of Autolab Metrohm
For this we pre define recipe files in the specific proprietary xml language and then manipulate measurement parameters via
configuration dicts. The dicts point to the files that are being uploaded to the potentiostat
The actions cover measuring, setting the cell on or off asking the potential or current and if the potentiostat is measuring

"""
import sys
sys.path.append('../driver')
sys.path.append('../config')
sys.path.append('../server')
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json
from typing import List
import os
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
config = import_module(sys.argv[1]).config
serverkey = sys.argv[2]

app = FastAPI(title="Echem AutolabDriver V2",
    description="This is a very fancy echem action server",
    version="2.0")

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None


@app.get("/autolab/measure/")
def measure(procedure:str,setpointjson: str,plot:str,onoffafter:str,safepath:str,filename:str, parseinstructions:str):
    """
    Measure a recipe and manipulate the parameters:

    - **measure_conf**: is explained in the echemprocedures folder
    """
    measure_conf = dict(procedure=procedure,
                        setpointjson=setpointjson,
                        plot=plot,
                        onoffafter=onoffafter,
                        safepath=safepath,
                        filename=filename,
                        parseinstructions=parseinstructions)
    
    res = requests.get("{}/autolabDriver/measure".format(poturl), 
                        params=measure_conf).json()
  
    retc = return_class(parameters= measure_conf,
                        data = res)
    return retc


@app.get("/autolab/ismeasuring/")
def ismeasuring():
    res = requests.get("{}/autolabDriver/ismeasuring".format(poturl)).json()
    retc = return_class(parameters= None,data = res)
    return retc

@app.get("/autolab/potential/")
def potential():
    res = requests.get("{}/autolabDriver/potential".format(poturl)).json()
    retc = return_class(parameters= None,data = res)
    return retc

@app.get("/autolab/current/")
def current():
    res = requests.get("{}/autolabDriver/current".format(poturl)).json()
    retc = return_class(parameters= None,data = res)
    return retc

@app.get("/autolab/setcurrentrange/")
def setCurrentRange(crange:str):
    res = requests.get("{}/autolabDriver/setcurrentrange".format(poturl),
                        params={'crange':crange}).json()
    retc = return_class(parameters= {'crange':crange},data = res)
    return retc

@app.get("/autolab/appliedpotential/")
def appliedPotential():
    res = requests.get("{}/autolabDriver/appliedpotential".format(poturl)).json()
    retc = return_class(parameters= None,data =res)
    return retc

@app.get("/autolab/cellonoff/")
def CellOnOff(onoff:str):
    res = requests.get("{}/autolabDriver/cellonoff".format(poturl),
                        params={'onoff':onoff}).json()
    retc = return_class(parameters= {'cellonoff':onoff},data = res)
    return retc

@app.get("/autolab/retrieve")
def retrieve(safepath: str, filename: str):
    conf = dict(safepath= safepath,filename = filename)
    res = requests.get("{}/autolabDriver/retrieve".format(poturl),
                        params=conf).json()
    retc = return_class(parameters= {'safepath':safepath,'filename':filename},data = res)
    return retc

if __name__ == "__main__":
    #poturl = "http://{}:{}".format(config['servers']['autolab']['host'], config['servers']['autolab']['port'])
    print('initialized autolab starting the server')
    #uvicorn.run(app, host=config['servers']['autolabDriver']['host'], port=config['servers']['autolabDriver']['port'])
    url = config[serverkey]['url']
    uvicorn.run(app, host=config['servers'][serverkey]['host'], 
                     port=config['servers'][serverkey]['port'])
    