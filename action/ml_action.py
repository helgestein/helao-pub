import sys
sys.path.append(r'../driver')
sys.path.append(r'../action')

import json
from pydantic import BaseModel
from fastapi import FastAPI
import uvicorn
from celery import group
from ml_driver import DataUtilSim

#import data_analysis.analysis_action as ana


app = FastAPI(title="analysis action server",
              description="This is a test measure action",
              version="1.0")


class return_class(BaseModel):
    parameters: dict = None
    data: dict = None


@app.get("/learning/gaus_model")
def gaus_model(length_scale: int = 1, restart_optimizer: int = 10, random_state: int = 42):
    model = d.gaus_model(length_scale, restart_optimizer, random_state)
    retc = return_class(parameters={'length_scale': length_scale, 'restart_optimizer': restart_optimizer, 'random_state': random_state}, data={
                        'model': model})
    return retc

# we still need to discuss about the data type that we are adding here.


@app.get("/learning/activeLearning")
def active_learning_random_forest_simulation(session: str, x_query: str, save_data_path: str = 'ml_data/ml_analysis.json', addresses: str = json.dumps(["moveSample/parameters", "schwefel_function/data/key_y"])):

    next_exp_pos, prediction = d.active_learning_random_forest_simulation(
        session, x_query, save_data_path, addresses)

    # next_exp_pos : would be a [dx, dy] of the next move
    # prediction : list of predicted schwefel function for the remaning positions
    print(next_exp_pos)
    return next_exp_pos, str(next_exp_pos), prediction


if __name__ == "__main__":
    d = DataUtilSim()
    url = "http://{}:{}".format(config['servers']['learningServer']
                                ['host'], config['servers']['learningServer']['port'])
    port = 13364
    host = "127.0.0.1"
    print('Port of ml Server: {}')
    uvicorn.run(app, host=config['servers']['learningServer']
                ['host'], port=config['servers']['learningServer']['port'])
    print("instantiated ml server")
