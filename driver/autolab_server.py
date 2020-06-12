#this is the server
import sys
sys.path.append(r"./config")
from autolab_driver import Autolab
import mischbares_small
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import json

app = FastAPI(title="Autolab server V1",
    description="This is a very fancy autolab server",
    version="1.0",)

class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None

@app.get("/potentiostat/disconnect")
def disconnect():
    a.disconnect()
    retc = return_class(measurement_type='potentiostat_autolab',
                        parameters= {'command':'disconnect',
                                    'parameters':None},
                        data = {'data':None})
    return retc

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
def setStability(stability):
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
def performMeasurement(conf: dict):
    a.performMeasurement(conf)
    if retrieve:
    retc = return_class(measurement_type='potentiostat_autolab',
                    parameters= {'command':'measure',
                                'parameters':conf},
                    data = {'appliedpotential':ret})
    return retc

@app.get("/potentiostat/retrieve")
def retrieve(conf: dict):
    path = os.path.join(conf['safepath'],conf['filename'])
    with open(path.replace('.nox', '_data.json'), 'r') as f:
        ret = json.dump(self.data, f)
    retc = return_class(measurement_type='potentiostat_autolab',
                    parameters= {'command':'retrieve',
                                'parameters':conf},
                    data = {'appliedpotential':ret})
    return retc

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=13371)
    autolab_conf = mischbares_small.config['autolab']
    a = Autolab(mischbares_small.config['autolab'])
