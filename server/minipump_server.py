import time
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import sys
sys.path.append('../driver')
sys.path.append('../config')
from mischbares_small import config
from minipump_driver import minipump

app = FastAPI(title="Pump server V1",
    description="This is a very fancy pump server",
    version="1.0",)

class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None

@app.on_event("shutdown")
@app.get("/minipump/stopPump")
def stopPump(read:bool=False):
    ret = p.stopPump(read)
    retc = return_class(parameters={"read":read},data=ret)
    return retc

@app.get("/minipump/primePump")
def primePump(volume:int, speed:int, direction:int=1, read:bool=False):
    ret = p.primePump(volume, speed, direction, read)
    retc = return_class(parameters={"volume": volume,"speed": speed,"direction": direction,"read": read,
                                    "units":{'volume':'µL','speed':'µL/s'}},
                        data=ret)
    return retc

@app.get("/minipump/runPump")
def runPump(read:bool=False):
    ret = p.runPump(read)
    retc = return_class(parameters={"read":read},data=ret)
    return retc

@app.get("/minipump/readPump")
def readPump():
    ret = p.readPump()
    retc = return_class(parameters=None,data=ret)
    return retc

@app.get("/minipump/read")
def read():
    ret = p.read()
    retc = return_class(parameters=None,data={'serial_response':ret})
    return retc


if __name__ == "__main__":
    p = minipump(config['minipump'])
    uvicorn.run(app, host=config['servers']['minipumpServer']['host'], port=config['servers']['minipumpServer']['port'])