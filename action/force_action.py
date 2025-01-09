#implement the action-server for force sensor
import sys
sys.path.append(r'../driver')
sys.path.append(r'../config')
sys.path.append(r'../server')
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import json
import requests
import os
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
config = import_module(sys.argv[1]).config
serverkey = sys.argv[2]

app = FastAPI(title="ForceDriver server V2", 
    description="This is a fancy forceDriver sensor action server", 
    version="2.0")


class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@app.get("/force/setzero")
def setzero():
    requests.get("{}/forceDriver/setzero".format(url)).json()
    retc = return_class(parameters=None, data=None)


@app.get("/force/read")
def read():
    #read a force measurement from the buffer. if there is no measurement in the buffer, it will wait for one to arrive.
    while True:
        data = requests.get("{}/forceDriver/read".format(url)).json()
        if data['data']['value'] != None:
            break
    retc = return_class(parameters=None, data=data)
    return retc



if __name__ == "__main__":
    url = config[serverkey]['url']
    uvicorn.run(app, host=config['servers'][serverkey]['host'], 
                     port=config['servers'][serverkey]['port'])  
    print("instantiated forceDriver sensor")
    