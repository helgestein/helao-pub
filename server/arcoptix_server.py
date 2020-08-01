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

@app.get("/arcoptix/connect")
def connect(self):
    data = str(a.connect())
    retc = return_class(measurement_type = "arcoptix_ftir_command",
                    parameters = {"command" : "connect"},
                    data = {"device" : data})
    return retc

@app.get("/arcoptix/spectrum")
def getSpectrum(self):
    data = a.getSpectrum()
    retc = return_class(measurement_type = "arcoptix_ftir_command",
                    parameters = {"command" : "get_spectrum"},
                    data = {"intensities" : data})
    return retc

@app.get("/arcoptix/wavelengths")
def getWavelengths(self):
    data = a.getWavelengths()
    retc = return_class(measurement_type = "arcoptix_ftir_command",
                    parameters = {"command" : "get_wavelengths"},
                    data = {"wavelengths" : data})
    return retc

@app.get("/arcoptix/wavenumbers")
def getWavenumbers(self):
    data = a.getWavenumbers()
    retc = return_class(measurement_type = "arcoptix_ftir_command",
                    parameters = {"command" : "get_wavenumbers"},
                    data = {"wavenumbers" : data})
    return retc

@app.get("/arcoptix/read")
def readSpectrum(self,av=1,):
    a.readSpectrum(av)
    retc = return_class(measurement_type = "arcoptix_ftir_command",
                    parameters = {"av" : av},
                    data = {"data" : None})
    return retc

@app.get("/arcoptix/readTime")
def readSpectrumTime(self,time):
    a.readSpectrumTime(time)
    retc = return_class(measurement_type = "arcoptix_ftir_command",
                    parameters = {"time" : time},
                    data = {"data" : None})
    return retc

if __name__ == "__main__":
    a = arcoptix(config['arcoptix'])
    uvicorn.run(app, host=config['servers']['arcoptixServer']['host'], port=config['servers']['arcoptixServer']['port'])
    print("instantiated ftir spectrometer")