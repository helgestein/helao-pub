import os
import sys
import json
from pydantic import BaseModel
import requests
import uvicorn
from fastapi import FastAPI
from importlib import import_module
from dataclasses import dataclass

helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
sys.path.append(os.path.join(helao_root, 'server'))

config = import_module(sys.argv[1]).config
server_key = sys.argv[2]

app = FastAPI(title="dobot server",
              description="Dobot action server to control a robot.",
              version="1.0")

@dataclass
class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@app.get("/dobot/moveJointAbsolute")
def move_joint_absolute(x: float, y: float, z: float, r: float):
    parameters = {"x": x, "y": y, "z": z, "r": r}
    response = requests.get(f"{url}/dobotDriver/move_joint_absolute", params=parameters).json()
    return return_class(parameters=parameters, data=response)


@app.get("/dobot/moveLinearAbsolute")
def move_linear_absolute(x: float, y: float, z: float, r: float):
    parameters = {"x": x, "y": y, "z": z, "r": r}
    response = requests.get(f"{url}/dobotDriver/move_linear_absolute", params=parameters).json()
    return return_class(parameters=parameters, data=response)


@app.get("/dobot/moveJointRelative")
def move_joint_relative(x: float, y: float, z: float, r: float):
    parameters = {"x": x, "y": y, "z": z, "r": r}
    response = requests.get(f"{url}/dobotDriver/move_joint_relative", params=parameters).json()
    return return_class(parameters=parameters, data=response)


@app.get("/dobot/moveLinearRelative")
def move_linear_relative(x: float, y: float, z: float, r: float):
    retl = []
    parameters = {"x": x, "y": y, "z": z, "r": r}
    lin_parameters = {"x": x, "y": y, "z": z, "r": 0}
    joint_parameters = {"x": 0, "y": 0, "z": 0, "r": r}
    response = requests.get(f"{url}/dobotDriver/move_linear_relative", params=lin_parameters).json()
    retl.append(response)
    response = requests.get(f"{url}/dobotDriver/move_joint_relative", params=joint_parameters).json()
    retl.append(response)
    return return_class(parameters=parameters, data=retl)

@app.get("/dobot/setJointSpeed")
def set_joint_speed(speed: int):
    parameters = {"speed": speed}
    response = requests.get(f"{url}/dobotDriver/set_joint_speed", params=parameters).json()
    return return_class(parameters=parameters, data=response)

@app.get("/dobot/setLinearSpeed")
def set_linear_speed(speed: int):
    parameters = {"speed": speed}
    response = requests.get(f"{url}/dobotDriver/set_linear_speed", params=parameters).json()
    return return_class(parameters=parameters, data=response)


@app.get("/dobot/getPos")
def get_pose():
    with open("log.txt", mode="a") as log:
        log.write("Application shutdown")
    response = requests.get(f"{url}/dobotDriver/pose").json()
    return return_class(data=response)


@app.get("/dobot/getAngles")
def get_angles():
    response = requests.get(f"{url}/dobotDriver/angles").json()
    return return_class(data=response)


@app.get("/dobot/getErrorID")
def get_error_id():
    response = requests.get(f"{url}/dobotDriver/error_id").json()
    return return_class(data=response)


@app.get("/dobot/openGripper")
def open_gripper():
    response = requests.get(f"{url}/dobotDriver/open_gripper").json()
    return return_class(data=response)


@app.get("/dobot/closeGripper")
def close_gripper():
    response = requests.get(f"{url}/dobotDriver/close_gripper").json()
    return return_class(data=response)


@app.get("/dobot/suck")
def suck():
    response = requests.get(f"{url}/dobotDriver/suck").json()
    return return_class(data=response)


@app.get("/dobot/unsuck")
def unsuck():
    response = requests.get(f"{url}/dobotDriver/unsuck").json()
    return return_class(data=response)


@app.get("/dobot/moveHome")
def move_home():
    parameters = {"x": config[server_key]["safe_home_pose"][0],
                  "y": config[server_key]["safe_home_pose"][1],
                  "z": config[server_key]["safe_home_pose"][2],
                  "r": config[server_key]["safe_home_pose"][3]}
    response = requests.get(f"{url}/dobotDriver/move_joint_absolute", params=parameters).json()
    return return_class(parameters=parameters, data=response)


@app.get("/dobot/moveWaste")
def move_waste(x: float = 0, y: float = 0, z: float = 0, r: float = 0):
    parameters = {"x": x + config[server_key]["safe_waste_pose"][0],
                  "y": y + config[server_key]["safe_waste_pose"][1],
                  "z": z + config[server_key]["safe_waste_pose"][2],
                  "r": r + config[server_key]["safe_waste_pose"][3]}
    response = requests.get(f"{url}/dobotDriver/move_joint_absolute", 
                            params=parameters).json()
    return return_class(parameters={"x": x, "y": y, "z": z, "r": r}, data=response)


@app.get("/dobot/moveSample")
def move_sample(x: float = 0, y: float = 0, z: float = 0, r: float = 0):
    parameters = {"x": x + config[server_key]["safe_sample_pose"][0],
                  "y": y + config[server_key]["safe_sample_pose"][1],
                  "z": z + config[server_key]["safe_sample_pose"][2],
                  "r": r + config[server_key]["safe_sample_pose"][3]}
    response = requests.get(f"{url}/dobotDriver/move_joint_absolute", 
                            params=parameters).json()
    return return_class(parameters={"x": x, "y": y, "z": z, "r": r}, data=response)

@app.get("/dobot/removeDrop")
def remove_drop(x: float = 0, y: float = 0, z: float = 0, r: float = 0):
    raw = []
    raw.append(requests.get(f"{url}/dobotDriver/move_joint_absolute",
                            params={"x": x + config[server_key]["remove_drop_pose"][0],
                                    "y": y + config[server_key]["remove_drop_pose"][1],
                                    "z": z + config[server_key]["safe_waste_pose"][2],
                                    "r": r + config[server_key]["remove_drop_pose"][3]}).json())
    raw.append(requests.get(f"{url}/dobotDriver/move_joint_absolute",
                            params={"x": x + config[server_key]["remove_drop_pose"][0],
                                    "y": y + config[server_key]["remove_drop_pose"][1],
                                    "z": z + config[server_key]["remove_drop_pose"][2],
                                    "r": r + config[server_key]["remove_drop_pose"][3]}).json())
    response = requests.get(f"{url}/dobotDriver/pose").json()
    raw.append(requests.get(f"{url}/dobotDriver/move_joint_absolute",
                            params={"x": x + config[server_key]["remove_drop_pose"][0],
                                    "y": y + config[server_key]["remove_drop_pose"][1],
                                    "z": z + config[server_key]["safe_waste_pose"][2],
                                    "r": r + config[server_key]["remove_drop_pose"][3]}).json())
    raw.append(response)
    return return_class(parameters={"x": x, "y": y, "z": z, "r": r}, data={"raw": raw, "response": response})

@app.get("/dobot/removeDropEdge")
def remove_drop(x: float = 0, y: float = 0, z: float = 0, r: float = 0):
    raw = []
    raw.append(requests.get(f"{url}/dobotDriver/move_joint_absolute",
                            params={"x": x + config[server_key]["safe_waste_pose"][0],
                                    "y": y + config[server_key]["safe_waste_pose"][1],
                                    "z": z + config[server_key]["remove_drop_pose"][2],
                                    "r": r + config[server_key]["remove_drop_pose"][3]}).json())
    raw.append(requests.get(f"{url}/dobotDriver/move_joint_absolute",
                            params={"x": x + config[server_key]["remove_drop_pose"][0],
                                    "y": y + config[server_key]["remove_drop_pose"][1],
                                    "z": z + config[server_key]["remove_drop_pose"][2],
                                    "r": r + config[server_key]["remove_drop_pose"][3]}).json())
    response = requests.get(f"{url}/dobotDriver/pose").json()
    raw.append(response)
    return return_class(parameters={"x": x, "y": y, "z": z, "r": r}, data={"raw": raw, "response": response})

@app.get("/dobot/moveDown")
def move_down(dz: float, steps: int, maxForce: float, threshold: float):
    steps = int(steps)
    force_value = []
    for i in range(steps):
        forceurl = config[server_key]['forceurl']
        response = requests.get("{}/force/read".format(forceurl), params=None).json()
        force_value.append(response)
        print(response['data']['data']['value'])
        if dz > threshold:
            if abs(response['data']['data']['value']) > maxForce:
                print('Max force reached!')
            move_linear_relative(x=0, y=0, z=-threshold, r=0)
            print('Step is more than the threshold')

        else:
            if not abs(response['data']['data']['value']) > maxForce:
                print('Max force not reached ...')
                move_linear_relative(x=0, y=0, z=-dz, r=0)
            else:
                print('Max force reached!')
        pos = get_pose()

    parameters = {"dz": dz, "steps": steps, "maxForce": maxForce, "threshold": threshold}
    data = {"pos": pos, "force_value": force_value}
    return return_class(parameters=parameters, data=data)


@app.get("/dobot/shutdown")
def shut_down():
    move_home()
    requests.get(f"{url}/dobotDriver/disconnect").json()


if __name__ == "__main__":
    url = config[server_key]['url']
    uvicorn.run(app, host=config['servers'][server_key]['host'],
                port=config['servers'][server_key]['port'])
    print("instantiated dobot action server")
