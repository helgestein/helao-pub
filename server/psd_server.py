import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import sys
import os
import asyncio
from importlib import import_module
from contextlib import asynccontextmanager
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
config = import_module(sys.argv[1]).config
serverkey = sys.argv[2]
#serverkey = 'psd'
#from driver.psd_driver import HamiltonPSD
from psd_driver import HamiltonPSD
#from config.sdc_cyan import config
#from sdc_cyan import config

app = FastAPI(title="Hamilton PSD/4 Syringe PumpDriver server V1",
    description="This is a very fancy syringe pump server",
    version="1.0")

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    yield
    p.shutdown()

@app.get("/psdDriver/pump")
def pump(step: int=0):
    ret = p.pump(step=step)
    retc = return_class(parameters={'step': step},
                                        data=dict())
    return retc

@app.get("/psdDriver/speed")
def def_speed(speed:int=10):
    ret = p.speed(speed=speed)
    retc = return_class(parameters={'speed': speed},
                                        data={})
    return retc

@app.get("/psdDriver/valve_number")
def valve(valve_number:int):
    ret = p.valve(valve_number=valve_number)
    retc = return_class(parameters={'valve_number': valve_number},
                                        data={})
    return retc

@app.get("/psdDriver/valve_angle")
def valve(valve_angle:int):
    ret = p.valve_angle(valve_angle=valve_angle)
    retc = return_class(parameters={'valve_angle': valve_angle},
                                        data={})
    return retc

@app.get("/psdDriver/angle")
def valve(valve:int):
    ret = p.valve(valve=valve)
    retc = return_class(parameters={'valve': valve},
                                        data={})
    return retc

@app.get("/psdDriver/read")
def read():
    ret_pos = p.query_syringe()
    ret_valve = p.query_valve()
    retc = return_class(parameters=dict(),
                        data={'pos': ret_pos, 'valve': ret_valve})
    return retc

if __name__ == "__main__":
    p = HamiltonPSD(config['psdDriver'])
    uvicorn.run(app, host=config['servers'][serverkey]['host'], port=config['servers'][serverkey]['port'])
    print("Terminated psdDriver")