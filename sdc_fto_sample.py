import numpy as np 
import itertools as it 
import requests
import json
import random
import sys
import time
sys.path.append(r'../config')
sys.path.append('config')
from sdc_4 import config

import os
import datetime

### path: 'safepath':'C:/Users/LaborRatte23-2/Documents/GitHub/helao-dev_2/temp'

def test_fnc(sequence,thread=0):
    server = 'orchestrator'
    action = 'addExperiment'
    params = dict(experiment=json.dumps(sequence),thread=thread)
    print("requesting")
    req_res = requests.post("http://{}:{}/{}/{}".format(
        config['servers']['orchestrator']['host'], 13380, server, action), params=params).json()
    return req_res

x, y = np.meshgrid([-5 * i - 5 for i in range(9)], [-5 * i - 5 for i in range(9)])
x, y = x.flatten(), y.flatten()