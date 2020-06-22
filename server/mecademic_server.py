import sys
sys.path.append(r"../config")
sys.path.append(r"../driver")
from mecademic_driver import Mecademic
import mischbares_small
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
    retc = return_class(
        measurement_type="mecademic_command",
        parameters={"command": "error_is_reset"},
        data={'status': True}
        )
    return retc 

@app.get("/mecademic/setTrf")
def set_trf(x: float, y: float, z: float, alpha: float, beta: float, gamma: float):
    m.set_tfr(x, y, z, alpha, beta, gamma)
    retc = return_class(
        measurement_type="mecademic_command",
        parameters={"command": "set-trf"},
        data={'data': "trf", "x": x, "y": y, "z": z, "alpha": alpha, "beta": beta, "gamma": gamma}
        )
    return retc 

@app.get("/mecademic/mvPosePlane")
def mvposeplane(x: float, y: float):
    m.mvposeplane(x, y)
    retc = return_class(
            measurement_type="mecademic_command",
            parameters={"command": "mvposeplane"},
            data={'data': "poses", "x": x, "y": y}
            )
    return retc 

@app.get("/mecademic/dMoveJoints")
def DMoveJoints(a: float, b: float, c: float, d: float, e: float, f: float):
    m.DMoveJoints(a, b, c, d, e, f)
    retc = return_class(
            measurement_type="mecademic_command",
            parameters={"command": "DMoveJoints"},
            data={'data': "joints" , "joint1": a, "joint2": b, "joint3": c, "joint4": d, "joint5": e, "joint6": f}
        )
    return retc

@app.get("/mecademic/dMoveLin")
def DMoveLin(a: float, b: float, c: float, d: float, e: float, f: float):
    m.DMoveLin(a, b, c, d, e, f)
    retc = return_class(
                measurement_type="mecademic_command",
                parameters={"command": "DMoveLin"},
                data={'data': "axes" , "axis1": a, "axis2": b, "axis3": c, "axis4": d, "axis5": e, "axis6": f}
            )
    return retc

@app.get("/mecademic/dMovePose")
def DMovePose(a: float, b: float, c: float, d: float, e: float, f: float):
    m.DMovePose(a, b, c, d, e, f)
    retc = return_class(
            measurement_type="mecademic_command",
            parameters={"command": "DMovePose"},
            data={'data': "poses", "pos1": a, "pos2": b, "pos3": c, "pos4": d, "pos5": e, "pos6": f}
        )
    return retc

@app.get("/mecademic/dqLinZ")
def DQLinZ(z: int=20,nsteps: int=100):
    m.DQLinZ(z, nsteps)
    retc = return_class(
            measurement_type="mecademic_command",
            parameters={"command": "DQLinZ"},
            data={"z": z, "step_num": nsteps}
            )
    return retc

@app.get("/mecademic/dqLinX")
def DQLinX(x: int=20, nsteps: int=100):
    m.DQLinX(x, nsteps)
    retc = return_class(
            measurement_type="mecademic_command",
            parameters={"command": "DQLinX"},
            data={"x": x, "step_num": nsteps}
            )
    return retc

@app.get("/mecademic/dqLinY")
def DQLinY(y: int=20, nsteps: int=100):
    m.DQLinY(y, nsteps)
    retc = return_class(
        measurement_type="mecademic_command",
        parameters={"command": "DQLinY"},
        data={"y": y, "step_num": nsteps}
        )
    return retc

@app.get("/mecademic/dGetPose")
def DGetPose():
    data= m.DGetPose()
    retc = return_class(
        measurement_type="mecademic_command",
        parameters={"command": "DGetPose"},
        data={"poses": data}
        )
    return retc

@app.get("/mecademic/dGetJoints")
def DGetJoints():
    data = m.DGetJoints()
    print(data)
    print(type(data))
    retc = return_class(
        measurement_type="mecademic_command",
        parameters={"command": "DGetJoints"},
        data={"joints": data}
        )
    return retc

@app.get("/mecademic/checkRobot")
def checkrobot():
    data = m.checkrobot()
    retc = return_class(
        measurement_type="mecademic_command",
        parameters={"command": "checkrobot"},
        data={"status": data}
        )
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
    m = Mecademic()
    uvicorn.run(app, host=config['servers']['mecademicServer']['host'], port=config['servers']['mecademicServer']['port'])
    print("instantiated mecademic")
    