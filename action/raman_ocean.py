#implement the action-server for ocean optics raman
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

app = FastAPI(title="ocean optics raman server V1", 
    description="This is a fancy ocean optics raman spectrometer action server", 
    version="1.0")


class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None


@app.get("/oceanAction/read")
def read(t:int,filename:str):
    data = requests.get("{}/ocean/readSpectrum".format(url),params={'t':t,'filename':filename}).json()
    retc = return_class(parameters={"filename":filename,"t":t,'units':{'t':'µs'}}, data=data)
    return retc

@app.get("/oceanAction/loadFile")
def loadFile(filename:str):
    data = requests.get("{}/ocean/loadFile".format(url),params={'filename':filename}).json()
    retc = return_class(parameters={'filename':filename}, data=data)
    return retc



if __name__ == "__main__":
    url = "http://{}:{}".format(config['servers']['oceanServer']['host'],config['servers']['oceanServer']['port'])
    uvicorn.run(app,host=config['servers']['smallRamanServer']['host'],port=config['servers']['smallRamanServer']['port'])
    print("instantiated ocean optics raman action")