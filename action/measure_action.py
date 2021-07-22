import sys
sys.path.append(r"../driver")
sys.path.append(r"../config")
if r"C:\Users\Fuzhi\Documents\GitHub\celery_task_queue" not in sys.path:
    sys.path.append(r"C:\Users\Fuzhi\Documents\GitHub\celery_task_queue")
import json
from pydantic import BaseModel
from fastapi import FastAPI
import uvicorn
from celery import group
import os
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(helao_root)
config = import_module(sys.argv[1]).config
from measure_driver import dataAnalysis
serverkey = sys.argv[2]

app = FastAPI(title="measure measureDriver V2",
              description="This is a test measure action",
              version="2.0")

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None


@app.get("/measureDriver/make_grid")
def make_grid(x_start: float, x_end: float, x_step: float, y_start: float, y_end: float, y_step: float, save_data_to: str = "../data/grid.json"):
    make_grid = d.make_grid.delay(x_start, x_end, x_step, y_start,
                                  y_end, y_step, save_data_to)
    comp = make_grid.get()
    retc = return_class(parameters={'x_start': x_start, 'x_end': x_end, 'x_step': x_step, 'y_start': y_start,
                                    'y_end': y_end, 'y_step': y_step}, data=comp)
    return retc


@app.get("/measureDriver/make_n_nary")
def make_n_nary(n: int, steps: int, save_data_to: str = "../data/quin.json"):
    n_nary_task = d.make_n_nary(n, steps, save_data_to)
    comp = n_nary_task
    retc = return_class(parameters={'n': n, 'steps': steps}, data=comp)
    return retc

# [dx,dy]


@app.get("/measureDriver/schwefelFunction")
def schwefel_function_single(x: float , y:float):
    ### input : x, y are a random point from our substrate
    f = d.schwefel_function(x,y)
    #result = f.get()
    retc = return_class(parameters={'x':x,'y':y}, data={
                        'key_y': f})
    return retc

###############put away the celery for the new version, to make the other part of infrastucture works first
@app.get("/measureDriver/schwefel_function_group")
def schwefel_function_group(n: int, steps: int = None, x_start: float = None, x_end: float = None, x_step: float = None, y_start: float = None,
                            y_end: float = None, y_step: float = None, save_data_to: str = "../data/schwefel_fnc_group.json"):
    if n == 2:
        make_grid = d.make_grid(x_start, x_end, x_step, y_start,
                                      y_end, y_step, save_data_to="../data/binary.json")
        grid_arr = make_grid
        f_task = [d.schwefel_function(vector_fnc='[{}, {}]'.format(x[0], x[1]), save_data_to="../data/schwefel_single.json") for x in grid_arr['steps']]

    if n == 3:
        n_nary_task = d.make_n_nary(3, steps, save_data_to="../data/ternary.json")
        comp = n_nary_task
        f_task = [d.schwefel_function(vector_fnc='[{},{},{}]'.format(x[0], x[1], x[2]), save_data_to="../data/schwefel_single.json") for x in comp['steps']]

    if n == 4:
        n_nary_task = d.make_n_nary(4, steps, save_data_to="../data/quaternary.json")
        comp = n_nary_task
        f_task = [d.schwefel_function(vector_fnc='[{}, {}, {}, {}]'.format(x[0], x[1], x[2], x[3]), save_data_to="../data/schwefel_single.json") for x in comp['data']['steps']]

    f = f_task
    print(f)
    result = f
    with open(save_data_to, 'w') as res:
        json.dump(result, res)
    retc = return_class(parameters={'n': n}, data={'schwefel': result})
    return retc


if __name__ == "__main__":
    d = dataAnalysis()
    #url = "http://{}:{}".format(config['servers']['measureDriver']
    #                            ['host'], config['servers']['measureDriver']['port'])

    #print('Port of measureDriver: {}')
    #uvicorn.run(app, host=config['servers']['measureDriver']
    #            ['host'], port=config['servers']['measureDriver']['port'])
    #print("instantiated measureDriver")
    url = config[serverkey]['url']
    uvicorn.run(app, host=config['servers'][serverkey]['host'], 
                     port=config['servers'][serverkey]['port'])