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

@app.get("/pump/isPumping")
def isBlocked(pump: int):
    ret = p.isBlocked(pump)
    retc = return_class(measurement_type="pump_command",
                        parameters={"command": "isBlocked"},
                        data={'status': ret})
    return retc

@app.get("/pump/setBlock")
def setBlock(pump:int, time_block:float):
    #this sets a block
    ret = p.setBlock(pump,time_block)
    retc = return_class(measurement_type="pump_command",
                        parameters={"command": "block","time_block":time_block},
                        data=None)
    return retc

#@app.get("/pump/dispenseVolume")
#def dispenseVolume(pump:int ,volume:int ,speed:int ,stage:bool=False, read:bool=False, direction:int=1):
#    ret = p.dispenseVolume(pump, volume, speed, stage, read, direction)
#    
#    retc = return_class(measurement_type="pump_command",
#                        parameters={"command": "dispenseVolume","parameters": {"volume": volume,"speed": speed,"pump": pump,"direction": direction}},
#                        data={'serial_response': ret})
#    return retc

@app.get("/pump/stopPump")
def stopPump(pump:int):
    ret = p.stopPump(pump)
    retc = return_class(measurement_type="pump_command",
                        parameters={"command": "stopPump","parameters": {"pump": pump,'speed': 0,'volume': 0,'direction': -1,"time_block": ret}},
                        data=None)
    return retc

#@app.get("/pump/allOn")
#def allOn():
#    p.allOn()
#    retc = return_class(measurement_type="pump_command",
#                        parameters={"command": "allOn","parameters": {"pump_primings":p.pumpPrimings}},
#                        data=None)
#    return retc

@app.get("/pump/primePump")
def primePump(pump:int, volume:int, speed:int, direction:int=1, read:bool=False):
    ret = p.primePump(pump, volume, speed, direction, read)
    retc = return_class(measurement_type="pump_command",
                        parameters={"command": "primePump","parameters": {"volume": volume,"speed": speed,"pump": pump,"direction": direction}},
                        data={'serial_response': ret})
    return retc

@app.get("/pump/runPump")
def runPump(pump:int):
    p.runPump(pump)
    retc = return_class(measurement_type="pump_command",
                        parameters={"command": "runPump","parameters": {"pump":pump}},
                        data=None)
    return retc

@app.get("/pump/getPrimings")
def getPrimings():
    ret = p.getPrimings()
    retc = return_class(measurement_type="pump_command",
                        parameters={"command": "getPrimings"},
                        data=ret)
    return retc

@app.get("/pump/refreshPrimings")
def getPrimings():
    p.refreshPrimings()
    retc = return_class(measurement_type="pump_command",
                        parameters={"command": "refreshPrimings"},
                        data=p.pumpPrimings)
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