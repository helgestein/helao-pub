#implement the analysis action
import sys
sys.path.append('..')
sys.path.append('../config')
sys.path.append('../driver')
sys.path.append('../action')
import uvicorn
from fastapi import FastAPI,BaseModel
import json
import requests
import os
import hdfdict
from util import highestName,dict_address
from measure_driver import dataAnalysis
from celery import group

app = FastAPI(title="Analysis server V1", 
description="This is a fancy analysis server", 
version="1.0")


class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

kadiurl = None
filepath = "C:/Users/jkflowers/Downloads"

@app.get("/analysis/dummy")
def bridge(exp_num: float, key_y: float, session: str):
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

    session = json.loads(session)
    data = interpret_input(session,"session","schwefel_function/data/key_y",experiment_number = int(exp_num))[0]


    #data = interpret_input(session,"session","dummy/data/key_y")
    retc = return_class(parameters={'exp_num': exp_num, 'key_y': key_y}, data=data)
    #{'key_x': 'measurement_no_{}/motor/moveSample_0'.format(exp_num), 'key_y': key_y})
    return retc


def interpret_input(sources:str,types:str,addresses:str,experiment_numbers=None):
    #sources is a single data source (jsonned object or file address) or a jsonned list of data sources
    #type is a string or jsonned list of strings telling you what data format(s) you are reading in
    #possible inputs: list of or individual kadi records, local files, the current session, pure data
    #source values for these: kadi id's, filepaths strings, a dictionary, a list or dictionary or whatever
    #type values for these: "kadi","file","session","pure"
    #well, actually, there will be no "file" type, instead, will need different codes for different file extensions ("json", "hdf5", etc.) (right now "hdf5" is the only one that works)
    #addresses tells you where in an HDF5 file to pull the data from, will be a single address or list of addresses
    #if data type is "pure", addresses will be None, as no processing is required.
    #if data is neither preprocessed nor in our standardized .hdf5 format, I guess I will have to modify this to accommodate later.
    #when we are working with an HDF5, as we should be in most cases, we will automatically iterate over every measurement number in the most recent session
    #addresses will tell us how to get from the measurment number root to each value we want
    #addresses will be a string of keys separated by /'s. the topmost key (action name) will ignore trailing numbers + underscore
    #if multiple of a single type of action are in the measurment, it will by default grab the lowest number; add "_i" to specify the (i+1)th lowest

    #we need the ability to only grab certain measurements from the input data source(s).
    #currently, I am going to have the choice defined by the integer "measurement_no" in the names of the given dictionary keys.
    #thus, the input "experiment_numbers", will comprise an integer or jsonned list thereof. 
    #this means that this feature probably won't be compatible with using multiple data sources at once, but for now, I do not think it needs to be.
    #when I have finished code which I can demonstrate, it should be easier to get intelligent feedback as to what would be a better standard.

    try:
        sources = json.loads(sources)
    except:
        pass
    try:
        types =  json.loads(types)
    except:
        pass
    try:
        addresses = json.loads(addresses)
    except:
        pass
    try:
        experiment_numbers = json.loads(experiment_numbers)
    except:
        pass

    if isinstance(types,str):
        sources,types = [sources],[types]
    if isinstance(addresses,str):
        addresses = [addresses]
    if isinstance(experiment_numbers,int) or experiment_numbers == None:
        experiment_numbers = [experiment_numbers]

    datas = []
    for source,typ in zip(sources,types):
        if typ == "kadi":
            requests.get(f"{kadiurl}/data/downloadfilesfromrecord",params={'ident':source,'filepath':filepath})
            source = os.path.join(filepath,source+".hdf5")
        if typ in ("kadi","hdf5"):
            source = dict(hdfdict.load(source,lazy=False,mode="r+"))
        if typ in ("kadi","hdf5","session"):
            data = []
            run = highestName(list(filter(lambda k: k != 'meta',source.keys())))
            #maybe it would be better to sort keys before iterating over them
            for key in source[run].keys():
                if key != 'meta' and (experiment_numbers == [None] or key.split('_')[-1] in experiment_numbers):
                    datum = []
                    for address in addresses:
                        #possibilities: address has no number and key(s) do
                        #               multiple numbered addresses and keys
                        topadd = address.split('/')[0].split('_')
                        actions = sorted(list(filter(lambda a: a.split('_')[0] == topadd[0],source[run][key].keys())),key=lambda a: int(a.split('_')[1]))
                        try:
                            if len(topadd) > 1:
                                action = actions[int(topadd[1])]
                            else: 
                                action = actions[0]
                            datum.append(dict_address('/'.join(address.split('/')[1:]),source[run][key][action]))
                        except:
                            print(f"item {key} does not have what we are looking for")
                    if datum != []:
                        data.append(datum)
            source = data
        if typ in ("kadi","hdf5","session","pure"):
            datas += source
    return datas

if __name__ == "__main__":
    d = dataAnalysis()
    port = 13369
    host = "127.0.0.1"
    print('Port of analysis Server: {}')
    uvicorn.run(app, host=host, port=port)
    print("instantiated analysis server")
