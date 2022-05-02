#implement the action-server for arcoptix ftir
import sys
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import datetime
import json
import requests
import os
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
config = import_module(sys.argv[1]).config
serverkey = sys.argv[2]

app = FastAPI(title="arcoptix ftir server V1", 
    description="This is a fancy arcoptix ftir spectrometer action server", 
    version="1.0")


class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@app.get("/arcoptix/read")
def read(filename:Optional[str]=None,time:bool=False,av:float=1,bg:bool=False,wlrange:str=None,wnrange:str=None,inrange:str=json.dumps([416,2501])):
    global background
    if filename == None:
        filename = 'arcoptixftir_'+datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    data = requests.get(f"{url}/arcoptixDriver/spectrum",params={'filename':filename,'time':time,'av':av,'wlrange':wlrange,'wnrange':wnrange,'inrange':inrange}).json()
    spectrum = {'wavelengths':[i*1000000000 for i in data['data']['wavelengths']],
                'wavenumbers':[i/100 for i in data['data']['wavenumbers']],
                'intensities':data['data']['intensities'],
                'units':{'wavelengths':'nm','wavenumbers':'1/cm','intensities':'counts'}}
    if bg:
        spectrum['intensities'] = [i-j for i,j in zip(spectrum['intensities'],background['intensities'])]
    retc = return_class(parameters={'filename':filename,'time':time,'av':av,'bg':bg,'wlrange':wlrange,'wnrange':wnrange,'inrange':inrange,'units':{"av":"s or #spectra"}}, 
                        data={'raw':data,'res':spectrum})
    return retc

@app.get("/arcoptix/setGain")
def setGain(gain:int):
    data = requests.get(f"{url}/arcoptixDriver/setGain",params={"gain":gain}).json()
    retc = return_class(parameters={"gain":gain},data=data)
    return retc

@app.get("/arctoptix/saturation")
def getSaturation():
    data = requests.get(f"{url}/arcoptixDriver/saturation",params=None).json()
    retc = return_class(parameters=None,data=data)
    return retc

@app.get("/arcoptix/getGain")
def getGain():
    data = requests.get(f"{url}/arcoptixDriver/getGain",params=None).json()
    retc = return_class(parameters=None,data=data)
    return retc

@app.get("/arcoptix/loadFile")
def loadFile(filename:str):
    data = requests.get(f"{url}/arcoptixDriver/loadFile",params={'filename':filename}).json()
    retc = return_class(parameters={'filename':filename}, data=data)
    return retc

@app.get("/arcoptix/readBackground")
def readBackground(filename:Optional[str]=None,time:bool=False,av:float=1,wlrange:str=None,wnrange:str=None,inrange:str=json.dumps([416,2501])):
    global background
    if filename == None:
        filename = 'arcoptixftir_'+datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    data = requests.get(f"{url}/arcoptixDriver/spectrum",params={'filename':filename,'time':time,'av':av,'wlrange':wlrange,'wnrange':wnrange,'inrange':inrange}).json()
    background = data['data']
    retc = return_class(parameters={'filename':filename,'time':time,'av':av,'wlrange':wlrange,'wnrange':wnrange,'inrange':inrange,'units':{"av":"s or #spectra"}}, 
                        data=data)
    return retc

@app.get("/arcoptix/loadBackground") 
def loadBackground(filename:str):
    global background
    data = requests.get(f"{url}/arcoptixDriver/loadFile",params={'filename':filename}).json()
    background = data['data']
    retc = return_class(parameters={'filename':filename}, data=data)
    return retc

@app.get("/arcoptix/getBackground") 
def getBackground(filename:str):
    global background
    retc = return_class(parameters={'filename':filename}, data=background)
    return retc

@app.on_event("startup")
def memory():
    global background
    background = {}

if __name__ == "__main__":
    url = config[serverkey]['url']
    uvicorn.run(app,host=config['servers'][serverkey]['host'],port=config['servers'][serverkey]['port'])