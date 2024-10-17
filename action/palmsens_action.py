import sys
sys.path.append('../driver')
sys.path.append('../config')
sys.path.append('../server')
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json
import numpy as np
from typing import List
import os
from importlib import import_module
from contextlib import asynccontextmanager
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
config = import_module(sys.argv[1]).config
serverkey = sys.argv[2]

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    yield

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

app = FastAPI(lifespan=app_lifespan, title="PalmSens v.1.0",
              description="This is a very fancy PalmSens Action server",
              version="1.0")

@app.get("/palmsens/measure/")
def measure(method:str, parameters:str, filename:str, substrate=None, id=None, experiment=None):

    params = json.loads(parameters)

    if method == "potentiostatic_impedance_spectroscopy":
        if params['e_dc'] == "None":
            path = config[serverkey]['path_json']
            fn = 'substrate_{}_ocp_{}_{}.json'.format(substrate, id, experiment)
            with open(os.path.join(path,fn),'r') as data:
                datafile = json.load(data)
                ocp_pot = sum(datafile["potential_arrays"][0][-10:])/10
                params['e_dc'] = ocp_pot

    if method == "chronopotentiometry":
        if 'e_max' in params:
            params['e_max'] /= 10
            params['e_max_bool'] = True
        if 'e_min' in params:
            params['e_min'] /= 10
            params['e_min_bool'] = True

    parameters = json.dumps(params)
    measure_conf = {"method": method, "parameters": parameters, "filename": filename}
    res = requests.get("{}/palmsensDriver/measure".format(poturl), 
                        params=measure_conf).json()
    
    retc = return_class(parameters = measure_conf,
                        data = res)
    return retc

@app.get("/palmsens/retrieveData/")
def retrieveData(filename:str):
    retrieve_conf = {"filename": filename}
    res = requests.get("{}/palmsensDriver/retrieveData".format(poturl), 
                        params=retrieve_conf).json()
    retc = return_class(parameters= retrieve_conf,
                        data = res)
    return retc

if __name__ == "__main__":
    print('Initialized PalmSens starting the server')
    poturl = config[serverkey]['url']
    uvicorn.run(app, host=config['servers'][serverkey]['host'], 
                     port=config['servers'][serverkey]['port'])
