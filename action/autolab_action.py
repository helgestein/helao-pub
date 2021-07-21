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

app = FastAPI(title="Echem AutolabDriver V2",
    description="This is a very fancy echem action server",
    version="2.0")

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None


@app.get("/autolabDriver/measure/")
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
    
    res = requests.get("{}/autolab/measure".format(poturl), 
                        params=measure_conf).json()
  
    retc = return_class(parameters= measure_conf,
                        data = res)
    return retc


@app.get("/autolabDriver/ismeasuring/")
def ismeasuring():
    res = requests.get("{}/autolab/ismeasuring".format(poturl)).json()
    retc = return_class(parameters= None,data = res)
    return retc

@app.get("/autolabDriver/potential/")
def potential():
    res = requests.get("{}/autolab/potential".format(poturl)).json()
    retc = return_class(parameters= None,data = res)
    return retc

@app.get("/autolabDriver/current/")
def current():
    res = requests.get("{}/autolab/current".format(poturl)).json()
    retc = return_class(parameters= None,data = res)
    return retc

@app.get("/autolabDriver/setcurrentrange/")
def setCurrentRange(crange:str):
    res = requests.get("{}/autolab/setcurrentrange".format(poturl),
                        params={'crange':crange}).json()
    retc = return_class(parameters= {'crange':crange},data = res)
    return retc

@app.get("/autolabDriver/appliedpotential/")
def appliedPotential():
    res = requests.get("{}/autolab/appliedpotential".format(poturl)).json()
    retc = return_class(parameters= None,data =res)
    return retc

@app.get("/autolabDriver/cellonoff/")
def CellOnOff(onoff:str):
    res = requests.get("{}/autolab/cellonoff".format(poturl),
                        params={'onoff':onoff}).json()
    retc = return_class(parameters= {'cellonoff':onoff},data = res)
    return retc

@app.get("/autolabDriver/retrieve")
def retrieve(safepath: str, filename: str):
    conf = dict(safepath= safepath,filename = filename)
    res = requests.get("{}/autolab/retrieve".format(poturl),
                        params=conf).json()
    retc = return_class(parameters= {'safepath':safepath,'filename':filename},data = res)
    return retc

if __name__ == "__main__":
    poturl = "http://{}:{}".format(config['servers']['autolab']['host'], config['servers']['autolab']['port'])
    print('initialized autolabDriver starting the server')
    uvicorn.run(app, host=config['servers']['autolabDriver']['host'], port=config['servers']['autolabDriver']['port'])