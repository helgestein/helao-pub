import time
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import sys
import os
from importlib import import_module
'''
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
config = import_module(sys.argv[1]).config
'''
sys.path.append(r'C:\Users\Helge Stein\Documents')

from hamilton_driver import Hamilton
#serverkey = sys.argv[2]

app = FastAPI(title="Hamilton Syringe PumpDriver server V1",
    description="This is a very fancy syringe pump server",
    version="1.0",)

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@app.get("/pumpDriver/pump")
def pump(leftVol:int=0,rightVol:int=0,leftPort:int=0,rightPort:int=0,delayLeft:int=0,delayRight:int=0):
    ret = p.pump(leftVol=leftVol,rightVol=rightVol,leftPort=leftPort,rightPort=rightPort,delayLeft=delayLeft,delayRight=delayRight)
    retc = return_class(parameters=dict(leftVol=leftVol,rightVol=rightVol,
                                        leftPort=leftPort,rightPort=rightPort,
                                        delayLeft=delayLeft,delayRight=delayRight),
                                        data=None)
    return retc

@app.get("/pumpDriver/getStatus")
def read():
    ret = p.getStatus()
    data = dict(volume_nL_left=ret['vl'],
                volume_nL_right=ret['vr'],
                valve_position_left=ret['vpl'],
                valve_position_right=ret['vpr'])
    retc = return_class(parameters=None,data=data)
    return retc

@app.on_event("shutdown")
def shutdown():
    p.shutdown()
    retc = return_class(parameters=None,data=None)
    return retc

if __name__ == "__main__":
    serverkey = 'hamiltonDriver'
    config = dict(hamilton_conf=dict(left=dict(syringe=dict(volume=5000000,
                                                    flowRate=1250000,
                                                    initFlowRate=625000),
                                        valve=dict(prefIn=1,prefOut=2)),
                            right=dict(syringe=dict(volume=5000000,
                                                    flowRate=1250000,
                                                    initFlowRate=625000),
                                        valve=dict(prefIn=1,prefOut=2))),
                 servers=dict(hamiltonDriver=dict(host="127.0.0.1", port=13479)))
    p = Hamilton(config['hamilton_conf'])
    uvicorn.run(app, host=config['servers'][serverkey]['host'], port=config['servers'][serverkey]['port'])
