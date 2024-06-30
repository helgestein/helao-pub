import requests
import json
import numpy as np
import pandas as pd
import random
import math
import sys
sys.path.append(r'../config')
sys.path.append('config')
from sdc_cyan import config
import matplotlib.pyplot as plt

def test_fnc(sequence, thread=0):
    server = 'orchestrator'
    action = 'addExperiment'
    params = dict(experiment=json.dumps(sequence),thread=thread)
    print("requesting")
    requests.post("http://{}:{}/{}/{}".format(
        config['servers']['orchestrator']['host'], 13390, server, action), params=params).json()
    
def orchestrator_test(action, thread=0):
    server = 'orchestrator'
    action = action
    params = dict(thread=thread)
    print("requesting")
    print(requests.post("http://{}:{}/{}/{}".format(
        config['servers']['orchestrator']['host'],config['servers']['orchestrator']['port'], server, action), params=params).json())
