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
def read():
    wavelengthData = requests.get("{}/ocean/wavelengths".format(url)).json()
    intensityData = requests.get("{}/ocean/intensities".format(url)).json()
    retc = return_class(measurement_type='raman_measure', 
                            parameters={'command':'read_data'}, 
                            data={'wavelengths':wavelengthData,'intensity':intensityData})
    return retc



if __name__ == "__main__":
    url = "http://{}:{}".format(config['servers']['oceanServer']['host'],config['servers']['oceanServer']['port'])
    uvicorn.run(app,host=config['servers']['smallRamanServer']['host'],port=config['servers']['smallRamanServer']['port'])
    print("instantiated ocean optics raman action")