#implement the action-server for ocean optics raman
import sys
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import datetime
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
def read(t:float,filename:Optional[str]=None,bg:bool=False):
    global background
    if filename == None:
        filename = 'oceanraman_'+datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    data = requests.get("{}/oceanDriver/readSpectrum".format(url),params={'t':int(t*1000000),'filename':filename}).json()
    spectrum = {}
    spectrum['wavenumbers'] = [10000000*(1/config[serverkey]['wavelength']-1/i) for i in data['data']['wavelengths']]
    spectrum['units'] = {'wavenumbers':'cm-1','intensities':'counts'}
    if bg:
        spectrum['intensities'] = [i - j for i,j in zip(data['data']['intensities'],background['intensities'])]
    else:
        spectrum['intensities'] = data['data']['intensities']
    retc = return_class(parameters={"filename":filename,"t":t,'units':{'t':'s'}}, data={'raw':data,'res':spectrum})
    return retc

@app.get("/ocean/loadFile")
def loadFile(filename:str):
    data = requests.get("{}/oceanDriver/loadFile".format(url),params={'filename':filename}).json()
    retc = return_class(parameters={'filename':filename}, data=data)
    return retc

@app.get("/ocean/readBackground")
def readBackground(t:float,filename:Optional[str]=None):
    global background
    if filename == None:
        filename = 'oceanraman_'+datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    data = requests.get("{}/oceanDriver/readSpectrum".format(url),params={'t':int(t*1000000),'filename':filename}).json()
    spectrum = {}
    spectrum['wavenumbers'] = [10000000*(1/config[serverkey]['wavelength']-1/i) for i in data['data']['wavelengths']]
    spectrum['units'] = {'wavenumbers':'cm-1','intensities':'counts'}
    spectrum['intensities'] = data['data']['intensities']
    background = spectrum
    retc = return_class(parameters={"filename":filename,"t":t,'units':{'t':'s'}}, data={'raw':data,'res':spectrum})
    return retc

@app.get("/ocean/loadBackground") 
def loadBackground(filename:str):
    global background
    data = requests.get("{}/oceanDriver/loadFile".format(url),params={'filename':filename}).json()
    background = data['data']
    retc = return_class(parameters={'filename':filename}, data=data)
    return retc

@app.get("/ocean/getBackground") 
def getBackground():
    global background
    retc = return_class(parameters=None, data=background)
    return retc

@app.on_event("startup")
def memory():
    global background
    background = {}
    


if __name__ == "__main__":
    url = config[serverkey]['url']
    uvicorn.run(app,host=config['servers'][serverkey]['host'],port=config['servers'][serverkey]['port'])