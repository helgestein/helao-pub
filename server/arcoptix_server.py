import sys
sys.path.append(r"..\config")
sys.path.append(r"..\driver")
from arcoptix_driver import arcoptix
from mischbares_small import config
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import json

app = FastAPI(title="ocean driver", 
            description= " this is a fancy arctoptix ftir spectrometer driver server",
            version= "1.0")


class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None



@app.get("/arcoptix/spectrumWavelengths")
def getSpectrumWavelengths(filename:str):
    data = a.getSpectrumWavelengths(filename)
    retc = return_class(measurement_type = "arcoptix_ftir_command",
                    parameters = {"filename" : filename},
                    data = data)
    return retc

@app.get("/arcoptix/spectrumWavenumbers")
def getSpectrumWavenumbers(filename:str):
    data = a.getSpectrumWavenumbers(filename)
    retc = return_class(measurement_type = "arcoptix_ftir_command",
                    parameters = {"filename" : filename},
                    data = data)
    return retc

@app.get("/arcoptix/read")
def readSpectrum(av:int=1):
    a.readSpectrum(av)
    retc = return_class(measurement_type = "arcoptix_ftir_command",
                    parameters = {"av" : av},
                    data = {"data" : None})
    return retc

@app.get("/arcoptix/readTime")
def readSpectrumTime(time:float):
    a.readSpectrumTime(time)
    retc = return_class(measurement_type = "arcoptix_ftir_command",
                    parameters = {"time" : time},
                    data = {"data" : None})
    return retc


@app.get("/arcoptix/loadFile")
def loadFile(filename:str):
    data = a.loadFile(filename)
    retc = return_class(measurement_type = "arcoptix_ftir_command",
                    parameters = {"filename" : filename},
                    data = {"data" : data})
    return retc

if __name__ == "__main__":
    a = arcoptix(config['arcoptix'])
    uvicorn.run(app, host=config['servers']['arcoptixServer']['host'], port=config['servers']['arcoptixServer']['port'])
    print("instantiated ftir spectrometer")