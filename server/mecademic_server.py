import sys
sys.path.append(r"./config")
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

@app.get("/mecademic/set_tool_refrence_frame")
def set_trf(x: float, y: float, z: float, alpha: float, beta: float, gamma: float):
    m.set_tfr(x, y, z, alpha, beta, gamma)
    retc = return_class(
        measurement_type="mecademic_command",
        parameters={"command": "tool_refrence_frame"},
        data={'data': "trf", "x": x, "y": y, "z": z, "alpha": alpha, "beta": beta, "gamma": gamma}
        )
    return retc 

@app.get("/mecademic/move_pose_plane")
def mvposeplane(x: float, y: float):
    m.mvposeplane(x, y)
    retc = return_class(
            measurement_type="mecademic_command",
            parameters={"command": "move_pos_plane"},
            data={'data': "poses", "x": x, "y": y}
            )
    return retc 

@app.get("/mecademic/move_joints")
def DMoveJoints(a: float, b: float, c: float, d: float, e: float, f: float):
    m.DMoveJoints(a, b, c, d, e, f)
    retc = return_class(
            measurement_type="mecademic_command",
            parameters={"command": "move_joints"},
            data={'data': "joints" , "joint1": a, "joint2": b, "joint3": c, "joint4": d, "joint5": e, "joint6": f}
        )
    return retc

@app.get("/mecademic/move_linear")
def DMoveLin(a: float, b: float, c: float, d: float, e: float, f: float):
    m.DMoveLin(a, b, c, d, e, f)
    retc = return_class(
                measurement_type="mecademic_command",
                parameters={"command": "move_linear"},
                data={'data': "axes" , "axis1": a, "axis2": b, "axis3": c, "axis4": d, "axis5": e, "axis6": f}
            )
    return retc

@app.get("/mecademic/move_pos")
def DMovePose(a: float, b: float, c: float, d: float, e: float, f: float):
    m.DMovePose(a, b, c, d, e, f)
    retc = return_class(
            measurement_type="mecademic_command",
            parameters={"command": "movepose"},
            data={'data': "poses", "pos1": a, "pos2": b, "pos3": c, "pos4": d, "pos5": e, "pos6": f}
        )
    return retc

@app.get("/mecademic/linear_in_z")
def DQLinZ(z: int=20,nsteps: int=100):
    m.DQLinZ(z, nsteps)
    retc = return_class(
            measurement_type="mecademic_command",
            parameters={"command": "linear_move_z"},
            data={"z": z, "step_num": nsteps}
            )
    return retc

@app.get("/mecademic/linear_in_x")
def DQLinX(x: int=20, nsteps: int=100):
    m.DQLinX(x, nsteps)
    retc = return_class(
            measurement_type="mecademic_command",
            parameters={"command": "linear_move_x"},
            data={"x": x, "step_num": nsteps}
            )
    return retc

@app.get("/mecademic/linear_in_y")
def DQLinY(y: int=20, nsteps: int=100):
    m.DQLinY(y, nsteps)
    retc = return_class(
        measurement_type="mecademic_command",
        parameters={"command": "linear_move_y"},
        data={"y": y, "step_num": nsteps}
        )
    return retc

@app.get("/mecademic/get_pose")
def DGetPose():
    data= m.DGetPose()
    retc = return_class(
        measurement_type="mecademic_command",
        parameters={"command": "Get_pos"},
        data={"poses": data}
        )
    return retc

@app.get("/mecademic/get_joints")
def DGetJoints():
    data = m.DGetJoints()
    print(data)
    print(type(data))
    retc = return_class(
        measurement_type="mecademic_command",
        parameters={"command": "get_joints"},
        data={"joints": data}
        )
    return retc

@app.get("/mecademic/check_robot")
def checkrobot():
    data = m.checkrobot()
    retc = return_class(
        measurement_type="mecademic_command",
        parameters={"command": "check_robot"},
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
    uvicorn.run(app, host="127.0.0.1", port=13371)
    print("instantiated mecademic")
    