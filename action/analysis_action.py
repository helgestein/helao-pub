#implement the analysis action
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

app = FastAPI(title="Analysis server V1", 
description="This is a fancy analysis server", 
version="1.0")

@app.get("analysis/demo")
def demo(sources:str):
    data = interpret_input(sources)

def interpret_input(sources:str):
    #possible inputs: list of or individual kadi records, local files, the current session, pure data
    #but on this end, the session and pure data will look similar?
    
    #figure out whether you are working with one or multiple data sources
    #i need rules to distinguish list of data sources from actual data lists. 
    #or could always package things in a list? would rather not.
    sources = json.loads(sources)
    #for each data source, figure out what type it is and treat it accordingly

def build_dataset(data):
    #we should have something that takes in a dictionary or a reference to one of our .hdf5's
    #and builds it into some kind of data matrix more appropriate for analysis.
    #I guess that the details of this will be different for each analysis, but that there will be some code common to all.
    pass

if __name__ == "__main__":
    #url = "http://{}:{}".format(config['servers']['kadiServer']['host'], config['servers']['kadiServer']['port'])

    uvicorn.run(app, host=config['servers']['analysisServer']['host'], port=config['servers']['analysisServer']['port'])
    print("instantiated analysis action")