#implement the learning action
import sys
sys.path.append('../driver')
sys.path.append('../config')
sys.path.append('../server')
from mischbares_small import config
import uvicorn
from fastapi import FastAPI
import json
import requests
import os

app = FastAPI(title="Learning action V1", 
description="This is a fancy learning server", 
version="1.0")

@app.get("learning/demo")
def demo(session:str,experiment:str):
    session = json.loads(session)
    experiment = json.loads(experiment)
    #so, again, how do we get the analysis here?
    #need the input to constrain the values which arbitrary parameters can take
    #this will not give with pydantic
    # need ot think how we want to give the data from orchestrator in the case that we did not want to use fastapi and just celery alone 

    for para in experiment['params']:
        for item in para:
            if item == '$' or '$' in item:
                item = 0
    return json.dumps(experiment)



if __name__ == "__main__":
    #url = "http://{}:{}".format(config['servers']['kadiServer']['host'], config['servers']['kadiServer']['port'])

    uvicorn.run(app, host=config['servers']['learningServer']['host'], port=config['servers']['learningServer']['port'])
    print("instantiated learning action")