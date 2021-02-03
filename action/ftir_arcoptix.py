#implement the action-server for arcoptix ftir
import sys
sys.path.append(r'../driver')
sys.path.append(r'../config')
sys.path.append(r'../server')
from mischbares_small import config
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import json
import requests


app = FastAPI(title="arcoptix ftir server V1", 
    description="This is a fancy arcoptix ftir spectrometer action server", 
    version="1.0")


class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None

@app.get("/ftir/read")
def read(filename:str,timeMode:bool=False,av:int=1,time:float=None):
    readstring = 'Time' if timeMode else ''
    readparams = {'time':time} if timeMode else {'av':av}
    call = requests.get("{}/arcoptix/read{}".format(url,readstring),params=readparams).json()
    spectrum = requests.get("{}/arcoptix/spectrum".format(url),params={'filename':filename}).json()
    retc = return_class(parameters={'timeMode':timeMode,'av':av,'time':time,'filename':filename,'units':{'time':'??'}}, 
                        data={'raw':[call,spectrum],'res':spectrum['data']})
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