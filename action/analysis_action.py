from measure_driver import dataAnalysis
from celery import group
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import json
import sys
sys.append(r'../driver')
sys.append(r'../action')


app = FastAPI(title="analysis action server",
              description="This is a test measure action",
              version="1.0")


class return_class(BaseModel):
    parameters: dict = None
    data: dict = None


@app.get("/analysis/dummy")
def bridge(exp_num: float, key_y: float):
    """For now this is just a pass throught function that can get the result from measure action file and feed to ml server

    Args:
        exp_num (float): [this is the experimental number]
        key_y (float): [This is the result that we get from schwefel function, calculated in the measure action] 

    Returns:
        [dictionaty]: [measurement area (x_pos, y_pos) and the schwefel function result]
    """
    # here we need to return the key_y which is the schwefel function result and the corresponded measurement area
    # i.e pos: (dx, dy) -> schwefel(dx, dy)
    # We need to get the index of the perfomed experiment

    retc = return_class(parameters={'exp_num': exp_num, 'key_y': key_y}, data={
                        'key_x': 'measurement_no_{}/motor/moveSample_0'.format(exp_num), 'key_y': key_y})
    return retc


if __name__ == "__main__":
    d = dataAnalysis()
    port = 13369
    host = "127.0.0.1"
    print('Port of analysis Server: {}')
    uvicorn.run(app, host=host, port=port)
    print("instantiated analysis server")
