import sys
sys.path.append(r"../config")
sys.path.append(r"../driver")
from mecademic_driver import Mecademic
from mischbares_small import config
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import json


app = FastAPI(title="Mecademic driver server V1",
    description="This is a fancy mecademic driver server",
    version="1.0")

class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None


@app.get("/mecademic/connect")
def auto_repair():
    m.auto_repair()
    retc = return_class(parameters=None,data=None)
    return retc 

@app.get("/mecademic/setTrf")
def set_trf(x: float, y: float, z: float, alpha: float, beta: float, gamma: float):
    m.set_tfr(x, y, z, alpha, beta, gamma)
    retc = return_class(parameters={"x": x, "y": y, "z": z, "alpha": alpha, "beta": beta, "gamma": gamma,
                                    "units":{"x":'mm',"y":'mm',"z":'mm',"alpha":'degrees',"beta":'degrees',"gamma":'degrees'}},
                        data=None)
    return retc 

@app.get("/mecademic/mvPosePlane")
def mvposeplane(x: float, y: float):
    m.mvposeplane(x, y)
    retc = return_class(parameters={"x": x, "y": y,'units':{'x':'mm','y':'mm'}},data=None)
    return retc 

@app.get("/mecademic/dMoveJoints")
def DMoveJoints(a: float, b: float, c: float, d: float, e: float, f: float):
    m.DMoveJoints(a, b, c, d, e, f)
    retc = return_class(
        parameters={"a": a, "b": b, "c": c, "d": d, "e": e, "f": f,
                    "units":{'a':'degrees','b':'degrees','c':'degrees','d':'degrees','e':'degrees','f':'degrees'}},
        data=None)
    return retc

@app.get("/mecademic/dMoveLin")
def DMoveLin(a: float, b: float, c: float, d: float, e: float, f: float):
    m.DMoveLin(a, b, c, d, e, f)
    retc = return_class(parameters={"a": a, "b": b, "c": c, "d": d, "e": e, "f": f,
                                    "units":{'a':'mm','b':'mm','c':'mm','d':'degrees','e':'degrees','f':'degrees'}},
                        data=None)
    return retc

@app.get("/mecademic/dMovePose")
def DMovePose(a: float, b: float, c: float, d: float, e: float, f: float):
    m.DMovePose(a, b, c, d, e, f)
    retc = return_class(parameters={"a": a, "b": b, "c": c, "d": d, "e": e, "f": f,
                                    "units":{'a':'mm','b':'mm','c':'mm','d':'degrees','e':'degrees','f':'degrees'}},
                        data=None)
    return retc

@app.get("/mecademic/dqLinZ")
def DQLinZ(z: float=20,nsteps: int=100):
    m.DQLinZ(z, nsteps)
    retc = return_class(parameters={"z": z, "step_num": nsteps,'units':{'z':'mm'}},data=None)
    return retc

@app.get("/mecademic/dqLinX")
def DQLinX(x: float=20, nsteps: int=100):
    m.DQLinX(x, nsteps)
    retc = return_class(parameters={"x": x, "step_num": nsteps,'units':{'x':'mm'}},data=None)
    return retc

@app.get("/mecademic/dqLinY")
def DQLinY(y: float=20, nsteps: int=100):
    m.DQLinY(y, nsteps)
    retc = return_class(parameters={"y": y, "step_num": nsteps,'units':{'y':'mm'}},data=None)
    return retc

@app.get("/mecademic/dGetPose")
def DGetPose():
    data= m.DGetPose()
    retc = return_class(parameters=None,data={'x':data[0],'y':data[1],'z':data[2],'alpha':data[3],'beta':[4],'gamma':[5],
                                              'units':{'x':'mm','y':'mm','z':'mm','alpha':'degrees','beta':'degrees','gamma':'degrees'}})
    return retc

@app.get("/mecademic/dGetJoints")
def DGetJoints():
    data = m.DGetJoints()
    print(data)
    print(type(data))
    retc = return_class(parameters=None,data={'a':data[0],'b':data[1],'c':data[2],'d':data[3],'e':[4],'f':[5],
                                              'units':{'a':'degrees','b':'degrees','c':'degrees','d':'degrees','e':'degrees','f':'degrees'}})
    return retc

@app.get("/mecademic/checkRobot")
def checkrobot():
    data = m.checkrobot()
    retc = return_class(parameters=None,data={"status": data})
    return retc

@app.on_event("shutdown")
def disconnect():
    m.disconnect()
    retc = return_class(parameters= None,data = None)
    return retc



if __name__ == "__main__":
    m = Mecademic()
    uvicorn.run(app, host=config['servers']['mecademicServer']['host'], port=config['servers']['mecademicServer']['port'])
    print("instantiated mecademic")
    