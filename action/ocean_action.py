#implement the action-server for ocean optics raman
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
serverkey = sys.argv[2]


app = FastAPI(title="ocean optics raman server V1", 
    description="This is a fancy ocean optics raman spectrometer action server", 
    version="1.0")


class return_class(BaseModel):
    parameters: dict = None
    data: dict = None


@app.get("/ocean/read")
def read(t:int,filename:str):
    data = requests.get("{}/oceanDriver/readSpectrum".format(url),params={'t':t,'filename':filename}).json()
    retc = return_class(parameters={"filename":filename,"t":t,'units':{'t':'µs'}}, data=data)
    return retc

@app.get("/ocean/loadFile")
def loadFile(filename:str):
    data = requests.get("{}/oceanDriver/loadFile".format(url),params={'filename':filename}).json()
    retc = return_class(parameters={'filename':filename}, data=data)
    return retc



if __name__ == "__main__":
    url = config[serverkey]['url']
    uvicorn.run(app,host=config['servers'][serverkey]['host'],port=config['servers'][serverkey]['port'])
    print("instantiated ocean optics raman action")