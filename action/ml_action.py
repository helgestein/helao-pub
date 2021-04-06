from ml_driver import DataUtilSim
#import data_analysis.analysis_action as ana
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


@app.get("/learning/gaus_model")
def gaus_model(length_scale: int = 1, restart_optimizer: int = 10, random_state: int = 42):
    model = d.gaus_model(length_scale, restart_optimizer, random_state)
    retc = return_class(parameters={'length_scale': length_scale, 'restart_optimizer': restart_optimizer, 'random_state': random_state}, data={
                        'model': model})
    return retc

# we still need to discuss about the data type that we are adding here.


@app.get("/learning/activeLearning")
def active_learning_random_forest_simulation(key_x: dict, key_y: dict, x_query: str, y_query: str, save_data_path: str = 'ml_data/ml_analysis.json'):
    next_exp_pos, prediction = d.active_learning_random_forest_simulation(
        key_x, key_y, x_query, y_query, save_data_path)

    retc = return_class(parameters={'key_x': key_x, 'key_y': key_y, 'x_query': x_query, 'y_query': y_query}, data={
                        'next_exp_pos': next_exp_pos, 'prediction': prediction})
    return retc


if __name__ == "__main__":
    d = DataUtilSim()
    url = "http://{}:{}".format(config['servers']['learningServer']['host'], config['servers']['learningServer']['port'])
    port = 13364
    host = "127.0.0.1"
    print('Port of ml Server: {}')
    uvicorn.run(app, host=config['servers']['learningServer']['host'], port=config['servers']['learningServer']['port'])
    print("instantiated ml server")
