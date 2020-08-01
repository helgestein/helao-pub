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
def read(rtime=False,wavenumbers=True,av=1,time=None):
    tstring = 'Time' if rtime else ''
    requests.get("{}/arcoptix/read{}".format(url,tstring),params={'time':time} if rtime else {'av':av}).json()
    xformat = 'wavenumbers' if wavenumbers else 'wavelengths'
    spectrumx = requests.get("{}/arcoptix/{}".format(url,xformat)).json()
    spectrumy = requests.get("{}/arcoptix/spectrum".format(url)).json()
    retc = return_class(measurement_type='ftir_measure', 
                        parameters={'rtime':rtime,'wavenumbers':wavenumbers,'av':av,'time':time}, 
                        data={xformat:spectrumx,'intensity':spectrumy})
    return retc

if __name__ == "__main__":
    url = "http://{}:{}".format(config['servers']['arcoptixServer']['host'],config['servers']['arcoptixServer']['port'])
    uvicorn.run(app,host=config['servers']['ftirServer']['host'],port=config['servers']['ftirServer']['port'])
    print("instantiated arcoptix ftir action")