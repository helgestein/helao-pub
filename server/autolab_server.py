#this is the server
import sys
sys.path.append("../config")
sys.path.append("../driver")
from autolab_driver import Autolab
from mischbares_small import config
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import json
from typing import List

app = FastAPI(title="Autolab server V1",
    description="This is a very fancy autolab server",
    version="1.0",)

class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None

@app.get("/potentiostat/ismeasuring")
def ismeasuring():
    ret = a.ismeasuring()
    retc = return_class(measurement_type='potentiostat_autolab',
                        parameters= {'command':'ismeasuring',
                                    'parameters':None},
                        data = {'ismeasuring':ret})
    return retc

@app.get("/potentiostat/potential")
def potential():
    ret = a.potential()
    retc = return_class(measurement_type='potentiostat_autolab',
                        parameters= {'command':'getpotential',
                                    'parameters':None},
                        data = {'potential':ret})
    return retc

@app.get("/potentiostat/current")
def current():
    ret = a.current()
    retc = return_class(measurement_type='potentiostat_autolab',
                        parameters= {'command':'getcurrent',
                                    'parameters':None},
                        data = {'current':ret})
    return retc

@app.get("/potentiostat/setcurrentrange")
def setCurrentRange(crange: str):
    a.setCurrentRange(crange)
    retc = return_class(measurement_type='potentiostat_autolab',
                        parameters= {'command':'setcurrentrange',
                                    'parameters':crange},
                        data = {'currentrange':crange})
    return retc

@app.get("/potentiostat/setstability")
def setStability(stability:str):
    a.setStability(stability)
    retc = return_class(measurement_type='potentiostat_autolab',
                        parameters= {'command':'setStability',
                                    'parameters':stability},
                        data = {'currentrange':stability})
    return retc

@app.get("/potentiostat/appliedpotential")
def appliedPotential():
    ret = a.appliedPotential()
    retc = return_class(measurement_type='potentiostat_autolab',
                        parameters= {'command':'appliedpotential',
                                    'parameters':None},
                        data = {'appliedpotential':ret})
    return retc

@app.get("/potentiostat/abort")
def abort():
    ret = a.abort()
    retc = return_class(measurement_type='potentiostat_autolab',
                        parameters= {'command':'abort',
                                    'parameters':None},
                        data = {'abort':True})

@app.get("/potentiostat/cellonoff")
def CellOnOff(onoff:str):
    a.CellOnOff(onoff)
    retc = return_class(measurement_type='potentiostat_autolab',
                        parameters= {'command':'cellonoff',
                                    'parameters':onoff},
                        data = {'onoff':onoff})
    return retc

@app.get("/potentiostat/measure")
def performMeasurement(procedure: str,setpoint_keys:List[str],setpoint_values:List[float],plot:str,onoffafter:str,safepath:str,filename:str):
    a.performMeasurement(procedure,setpoint_keys,setpoint_values,plot,onoffafter,safepath,filename)
    retc = return_class(measurement_type='potentiostat_autolab',
                    parameters= {'command':'measure',
                                'parameters':dict(procedure=procedure,setpoint_keys=setpoint_keys,setpoint_values=setpoint_values,
                                                  plot=plot,onoffafter=onoffafter,safepath=safepath,filename=filename)},
                    data = {'data':None})
    return retc

@app.get("/potentiostat/retrieve")
def retrieve(safepath:str,filename:str):
    conf = dict(safepath=safepath,filename=filename)
    path = os.path.join(conf['safepath'],conf['filename'])
    with open(path.replace('.nox', '_data.json'), 'r') as f:
        ret = json.load(f)
    retc = return_class(measurement_type='potentiostat_autolab',
                    parameters= {'command':'retrieve',
                                'parameters':conf},
                    data = {'appliedpotential':ret})
    return retc

@app.on_event("shutdown")
def disconnect():
    a.disconnect()
    retc = return_class(measurement_type='potentiostat_autolab',
                        parameters= {'command':'disconnect',
                                    'parameters':None},
                        data = {'data':None})
    return retc

if __name__ == "__main__":
    autolab_conf = config['autolab']
    a = Autolab(config['autolab'])
    uvicorn.run(app, host=config['servers']['autolabServer']['host'], port=config['servers']['autolabServer']['port'])
