import sys
sys.path.append(r'..\driver')
sys.path.append(r'..\server')
sys.path.append(r'..\config')
import os
import time
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
config = import_module(sys.argv[1]).config
#from sdc_4 import config
from minipump_driver import minipump
serverkey = sys.argv[2]
#serverkey= 'minipumpDriver'

app = FastAPI(title="Pump server V2",
    description="This is a very fancy pump server",
    version="2.0",)

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@app.on_event("shutdown")
@app.get("/minipumpDriver/stopPump")
def stopPump(read:bool=False):
    ret = p.stopPump(read)
    retc = return_class(parameters={"read":read},data={'serial_response':ret})
    return retc

@app.get("/minipumpDriver/primePump")
def primePump(volume:int, speed:int, direction:int=1, read:bool=False):
    ret = p.primePump(volume, speed, direction, read)
    retc = return_class(parameters={"volume": volume,"speed": speed,"direction": direction,"read": read,
                                    "units":{'volume':'µL','speed':'µL/s'}},
                        data={'serial_response':ret})
    return retc

@app.get("/minipumpDriver/runPump")
def runPump(read:bool=False):
    ret = p.runPump(read)
    retc = return_class(parameters={"read":read},data={'serial_response':ret})
    return retc

@app.get("/minipumpDriver/readPump")
def readPump():
    ret = p.readPump()
    retc = return_class(parameters=None,data={'serial_response':ret})
    return retc

@app.get("/minipumpDriver/read")
def read():
    ret = p.read()
    retc = return_class(parameters=None,data={'serial_response':ret})
    return retc


if __name__ == "__main__":
    p = minipump(config[serverkey])
    uvicorn.run(app, host=config['servers'][serverkey]['host'], port=config['servers'][serverkey]['port'])
    #conf = dict(port='COM4', baud=1200, timeout=1)
    #p = minipump(conf)
    #uvicorn.run(app, host="127.0.0.1", port=13386)