import sys
sys.path.append(r"..\config")
sys.path.append(r"..\driver")
from ocean_driver import ocean
from mischbares_small import config
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import json


app = FastAPI(title="ocean driver", 
            description= " this is a fancy ocean optics raman spectrometer driver server",
            version= "1.0")


class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None

@app.get("/ocean/find")
def findDevice():
    device = o.findDevice()
    retc = return_class(measurement_type = "ocean_raman_command",
                        parameters = {"command" : "find_device"},
                        data = {"device" : str(device)})
    return retc

@app.get("/ocean/connect")
def open():
    o.open()
    retc = return_class(measurement_type = "ocean_raman_command",
                        parameters = {"command" : "open"},
                        data = {"status" : "activated"})
    return retc

@app.get("/ocean/wavelengths")
def getWavelengths():
    data = o.getWavelengths()
    retc = return_class(measurement_type = "ocean_raman_command",
                        parameters = {"command" : "get_wavelengths"},
                        data = {"wavelengths" : data.tolist()})
    return retc

@app.get("/ocean/intensities")
def getIntensities():
    data = o.getIntensities()
    retc = return_class(measurement_type = "ocean_raman_command",
                        parameters = {"command" : "get_intensities"},
                        data = {"intensities" : data.tolist()})
    return retc

@app.on_event("shutdown")
def close(self):
    o.close()
    retc = return_class(measurement_type = "ocean_raman_command",
                        parameters = {"command" : "close"},
                        data = {"status" : "deactivated"})
    return retc


if __name__ == "__main__":
    o = ocean()
    uvicorn.run(app, host=config['servers']['oceanServer']['host'], port=config['servers']['oceanServer']['port'])
    print("instantiated raman spectrometer")