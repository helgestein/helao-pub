import serial
import time
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import sys
sys.path.append('../driver')
from pump_driver import pump

app = FastAPI(title="Pump server V1",
    description="This is a very fancy pump server",
    version="1.0",)

class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None

@app.get("/pump/ispumping")
def isBlocked(pump: int):
    ret = p.isBlocked(pump)
    retc = return_class(**ret)
    return retc

@app.get("/pump/setBlock")
def setBlock(pump:int, time_block:float):
    #this sets a block
    ret = p.setBlock(pump,time_block)
    retc = return_class(**ret)
    return retc

@app.get("/pump/dispenseVolume")
def dispenseVolume(pump:int ,volume:int ,speed:int ,stage:bool=False, read:bool=False, direction:int=1):
    ret = p.dispenseVolume(pump, volume, speed, direction, read)
    retc = return_class(**ret)
    return retc

@app.get("/pump/stopPump")
def stopPump(pump:int):
    ret = p.stopPump(pump)
    retc = return_class(**ret)
    return retc

@app.get("/pump/allOn")
def allOn(time:int):
    ret = p.allOn(time)
    retc = return_class(**ret)
    return retc

@app.on_event("shutdown")
def shutdown():
    ret = p.shutdown()
    retc = return_class(**ret)
    return retc

if __name__ == "__main__":
    p = pump()
    uvicorn.run(app, host="127.0.0.1", port=13370)