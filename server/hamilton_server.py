import time
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import sys
import os
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
config = import_module(sys.argv[1]).config
serverkey = sys.argv[2]
from hamilton_driver import Hamilton
from contextlib import asynccontextmanager

app = FastAPI(title="Hamilton Microlab600 Syringe PumpDriver server V1",
    description="This is a very fancy syringe pump server",
    version="1.0",)

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@app.get("/hamiltonDriver/pump")
def pump(leftVol:int=0,rightVol:int=0,leftPort:int=0,rightPort:int=0,delayLeft:int=0,delayRight:int=0):
    ret = p.pump(leftVol=leftVol,rightVol=rightVol,leftPort=leftPort,rightPort=rightPort,delayLeft=delayLeft,delayRight=delayRight)
    retc = return_class(parameters=dict(leftVol=leftVol,rightVol=rightVol,
                                        leftPort=leftPort,rightPort=rightPort,
                                        delayLeft=delayLeft,delayRight=delayRight),
                                        data=None)
    return retc

@app.get("/hamiltonDriver/getStatus")
def read():
    ret = p.getStatus()
    data = dict(volume_nL_left=ret['vl'],
                volume_nL_right=ret['vr'],
                valve_position_left=ret['vpl'],
                valve_position_right=ret['vpr'])
    retc = return_class(parameters=None,data=data)
    return retc

#@app.on_event("shutdown")
#def shutdown():
#    p.shutdown()
#    retc = return_class(parameters=None,data=None)
#    return retc

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    yield
    p.shutdown()

if __name__ == "__main__":
    p = Hamilton(config['hamiltonDriver'])
    uvicorn.run(app, host=config['servers'][serverkey]['host'], port=config['servers'][serverkey]['port'])
