#implement the action-server for arcoptix ftir
import sys
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


app = FastAPI(title="arcoptix ftir server V1", 
    description="This is a fancy arcoptix ftir spectrometer action server", 
    version="1.0")


class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@app.get("/ftir/read")
def read(filename:str,time:bool=False,av:float=1,wlrange:str=None,wnrange:str=None,inrange:str=json.dumps([416,2501])):
    data = requests.get("{}/arcoptix/spectrum".format(url),params={'filename':filename,'time':time,'av':av,'wlrange':wlrange,'wnrange':wnrange,'inrange':inrange}).json()
    retc = return_class(parameters={'filename':filename,'time':time,'av':av,'wlrange':wlrange,'wnrange':wnrange,'inrange':inrange,'units':{"av":"s or #spectra"}}, 
                        data=data)
    return retc

@app.get("/ftir/setGain")
def setGain(gain:int):
    data = requests.get("{}/arcoptix/setGain".format(url),params={"gain":gain}).json()
    retc = return_class(parameters={"gain":gain},data=None)
    return retc

@app.get("/ftir/saturation")
def getSaturation():
    data = requests.get("{}/arcoptix/saturation".format(url),params=None).json()
    retc = return_class(parameters=None,data={"saturation":data})
    return retc

@app.get("/ftir/getGain")
def getGain():
    data = requests.get("{}/arcoptix/getGain".format(url),params=None).json()
    retc = return_class(parameters=None,data={"gain":data})
    return retc

@app.get("/ftir/loadFile")
def loadFile(filename:str):
    data = requests.get("{}/arcoptix/loadFile".format(url),params={'filename':filename}).json()
    retc = return_class(parameters={'filename':filename}, data=data)
    return retc


if __name__ == "__main__":
    url = "http://{}:{}".format(config['servers']['arcoptixServer']['host'],config['servers']['arcoptixServer']['port'])
    uvicorn.run(app,host=config['servers']['ftirServer']['host'],port=config['servers']['ftirServer']['port'])
    print("instantiated arcoptix ftir action")