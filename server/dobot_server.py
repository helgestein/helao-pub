import os
import sys
import json
import uvicorn
from fastapi import FastAPI
from importlib import import_module
from dataclasses import dataclass
from pydantic import BaseModel

helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
sys.path.append(os.path.join(helao_root, 'server'))

from dobot_driver import dobot, EndEffectorType

config = import_module(sys.argv[1]).config
server_key = sys.argv[2]

app = FastAPI(title="dobot server",
              description="Dobot server to control a robot.",
              version="1.0")

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None


@app.get("/dobotDriver/connect")
def connect():
    driver.connect()
    return return_class()


@app.get("/dobotDriver/init")
def init():
    driver.init()
    return return_class()


@app.get("/dobotDriver/is_alive")
def is_alive():
    alive = driver.is_alive()
    return return_class(data={'alive': alive})


@app.get("/dobotDriver/reconnect")
def reconnect():
    driver.reconnect()
    return return_class()


@app.get("/dobotDriver/disconnect")
def disconnect():
    driver.disconnect()
    return return_class()


@app.get("/dobotDriver/clear_error")
def clear_error():
    driver.clear_error()
    return return_class()


@app.get("/dobotDriver/set_end_effector")
def set_end_effector(id: int):
    driver.set_end_effector(EndEffectorType(id))
    return return_class(parameters={'id': id})


@app.get("/dobotDriver/set_end_effector_pins")
def set_end_effector_pins(pins: str):
    driver.set_end_effector_pins(json.loads(pins))
    return return_class(parameters={"pins": pins})


@app.get("/dobotDriver/set_end_effector_state")
def set_end_effector_state(state: int):
    driver.set_end_effector_state(state)
    return return_class(parameters={"state": state})


@app.get("/dobotDriver/set_digital_output")
def set_digital_output(pin: int, value: int):
    driver.set_digital_output(pin, value)
    return return_class(parameters={"pin": pin, "value": value})


@app.get("/dobotDriver/open_gripper")
def open_gripper():
    driver.open_gripper()
    return return_class()


@app.get("/dobotDriver/close_gripper")
def close_gripper():
    driver.close_gripper()
    return return_class()


@app.get("/dobotDriver/suck")
def suck():
    driver.suck()
    return return_class()


@app.get("/dobotDriver/unsuck")
def unsuck():
    driver.unsuck()
    return return_class()


@app.get("/dobotDriver/move_joint_absolute")
def move_joint_absolute(x: float, y: float, z: float, r: float):
    response = driver.nonblocking_move(driver.move_joint_absolute, [x, y, z, r])
    return return_class(parameters={'x': x, 'y': y, 'z': z, 'r': r}, data={'response': response})


@app.get("/dobotDriver/move_linear_absolute")
def move_linear_absolute(x: float, y: float, z: float, r: float):
    response = driver.nonblocking_move(driver.move_linear_absolute, [x, y, z, r])
    return return_class(parameters={'x': x, 'y': y, 'z': z, 'r': r}, data={'response': response})


@app.get("/dobotDriver/move_joint_relative")
def move_joint_relative(x: float, y: float, z: float, r: float):
    movement = driver.bound_movement([x, y, z, r])
    response = driver.nonblocking_move(driver.move_joint_relative, movement)
    return return_class(parameters={'x': x, 'y': y, 'z': z, 'r': r}, data={'response': response})


@app.get("/dobotDriver/move_linear_relative")
def move_linear_relative(x: float, y: float, z: float, r: float):
    movement = driver.bound_movement([x, y, z, r])
    response = driver.nonblocking_move(driver.move_linear_relative, movement)
    return return_class(parameters={'x': x, 'y': y, 'z': z, 'r': r}, data={'response': response})


@app.get("/dobotDriver/set_joint_speed")
def set_joint_speed(speed: int):
    driver.set_joint_speed(speed)
    return return_class(parameters={'speed': speed})


@app.get("/dobotDriver/set_linear_speed")
def set_linear_speed(speed: int):
    driver.set_linear_speed(speed)
    return return_class(parameters={'speed': speed})


@app.get("/dobotDriver/pose")
def get_pose():
    pose = (driver.pose).tolist()
    return return_class(data={'pose': pose})


@app.get("/dobotDriver/angles")
def get_angles():
    angles = (driver.angles).tolist()
    return return_class(data={'angles': angles})


@app.get("/dobotDriver/error_id")
def get_error_id():
    error_id = driver.error_id
    return return_class(data={'error_id': error_id})


if __name__ == "__main__":
    driver = dobot(config[server_key])
    uvicorn.run(app, host=config['servers'][server_key]['host'],
                port=config['servers'][server_key]['port'])
    print("instantiated dobot robot")
