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
from mischbares_small import config
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json
from typing import List

app = FastAPI(title="Echem Action server V1",
    description="This is a very fancy echem action server",
    version="1.0",)

class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None

@app.get("/echem/measure/")
def measure(procedure:str,setpoint_keys:List[str],setpoint_values:List[float],plot:str,onoffafter:str,safepath:str,filename:str):
    """
    Measure a recipe and manipulate the parameters:

    - **measure_conf**: is explained in the echemprocedures folder
    """
    measure_conf = dict(procedure=procedure,setpoint_keys=setpoint_keys,setpoint_values=setpoint_values,
                        plot=plot,onoffafter=onoffafter,safepath=safepath,filename=filename)
    
    res = requests.get("{}/potentiostat/measure".format(poturl), 
                        params=measure_conf).json()
  
    retc = return_class(measurement_type='echem_measure',
                        parameters= {'command':'measure',
                                    'parameters':measure_conf},
                        data = {'data':res})
    return retc

@app.get("/echem/ismeasuring/")
def ismeasuring():
    res = requests.get("{}/potentiostat/ismeasuring".format(poturl)).json()
    retc = return_class(measurement_type='echem_ismeasuring',
                        parameters= {'command':'ismeasuring',
                                    'parameters':None},
                        data = {'data':res})
    return retc

@app.get("/echem/potential/")
def potential():
    res = requests.get("{}/potentiostat/potential".format(poturl)).json()
    retc = return_class(measurement_type='echem_potential',
                        parameters= {'command':'potential',
                                    'parameters':None},
                        data = {'data':res})
    return retc

@app.get("/echem/current/")
def current():
    res = requests.get("{}/potentiostat/current".format(poturl)).json()
    retc = return_class(measurement_type='echem_current',
                        parameters= {'command':'current',
                                    'parameters':None},
                        data = {'data':res})
    return retc

@app.get("/echem/setcurrentrange/")
def setCurrentRange(crange:str):
    res = requests.get("{}/potentiostat/setcurrentrange".format(poturl),
                        params={'crange':crange}).json()
    retc = return_class(measurement_type='echem_setcurrentrange',
                        parameters= {'command':'setcurrentrange',
                                    'parameters':{'crange':crange}},
                        data = {'data':res})
    return retc

@app.get("/echem/appliedpotential/")
def appliedPotential():
    res = requests.get("{}/potentiostat/appliedpotential".format(poturl)).json()
    retc = return_class(measurement_type='echem_appliedpotential',
                        parameters= {'command':'appliedpotential',
                                    'parameters':None},
                        data = {'data':res})
    return retc

@app.get("/echem/cellonoff/")
def CellOnOff(onoff:str):
    res = requests.get("{}/potentiostat/cellonoff".format(poturl),
                        params={'onoff':onoff}).json()
    retc = return_class(measurement_type='echem_onoff',
                        parameters= {'command':'onoff',
                                    'parameters':{'cellonoff':onoff}},
                        data = {'data':res})
    return retc

@app.get("/echem/retrieve")
def retrieve(safepath: str, filename: str):
    conf = dict(safepath= safepath,filename = filename)
    res = requests.get("{}/potentiostat/retrieve".format(poturl),
                        params=conf).json()
    retc = return_class(measurement_type='echem_retrieve',
                        parameters= {'command':'retrieve',
                                    'parameters':{'retrieve':conf}},
                        data = {'data':res})
    return retc

if __name__ == "__main__":
    poturl = "http://{}:{}".format(config['servers']['autolabServer']['host'], config['servers']['autolabServer']['port'])
    print('initialized autolab starting the server')
    uvicorn.run(app, host=config['servers']['echemServer']['host'], 
                     port=config['servers']['echemServer']['port'])