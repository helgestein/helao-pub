import time
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import sys
sys.path.append('../driver')
sys.path.append('../config')
from mischbares_small import config
from pump_driver import pump

app = FastAPI(title="Pump server V1",
    description="This is a very fancy pump server",
    version="1.0",)

class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None

@app.get("/pump/stopPump")
def stopPump(pump:int,read:bool=False):
    ret = p.stopPump(pump,read)
    retc = return_class(measurement_type="pump_command",
                        parameters={"command": "stopPump","parameters": {"pump": pump,"read":read}},
                        data={'serial_response': ret})
    return retc

@app.get("/pump/primePump")
def primePump(pump:int, volume:int, speed:int, direction:int=1, read:bool=False):
    ret = p.primePump(pump, volume, speed, direction, read)
    retc = return_class(measurement_type="pump_command",
                        parameters={"command": "primePump","parameters": {"volume": volume,"speed": speed,"pump": pump,"direction": direction,"read": read}},
                        data={'serial_response': ret})
    return retc

@app.get("/pump/runPump")
def runPump(pump:int,read:bool=False):
    ret = p.runPump(pump,read)
    retc = return_class(measurement_type="pump_command",
                        parameters={"command": "runPump","parameters": {"pump":pump,"read":read}},
                        data={'serial_response': ret})
    return retc

@app.get("/pump/readPump")
def readPump(pump:int):
    ret = p.readPump(pump)
    retc = return_class(measurement_type="pump_command",
                        parameters={"command": "readPump","parameters": {"pump": pump}},
                        data=ret)
    return retc

@app.get("/pump/pumpOff")
def pumpOff(pump:int,read:bool=False):
    ret = p.pumpOff(pump,read)
    retc = return_class(measurement_type="pump_command",
                        parameters={"command": "pumpOff","parameters": {"pump": pump,"read":read}},
                        data={'serial_response': ret})
    return retc

@app.get("/pump/read")
def read():
    ret = p.read()
    retc = return_class(measurement_type="pump_command",
                        parameters={"command": "read"},
                        data={'data':ret})
    return retc

@app.on_event("shutdown")
def shutdown():
    ret = p.shutdown()
    retc = return_class(measurement_type="pump_command",
                        parameters={"command": "shutdown"},
                        data={'data':'shutdown'})
    return retc

if __name__ == "__main__":
    p = pump(config['pump'])
    uvicorn.run(app, host=config['servers']['pumpServer']['host'], port=config['servers']['pumpServer']['port'])