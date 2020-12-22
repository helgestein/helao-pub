import os
import sys
sys.path.append("../action")
import kadi_action as ka
from mischbares_small import config
import requests
import json

if __name__ == "__main__":
    i=0
    filepath = "C:/Users/jkflowers/Desktop/data2/data"
    soe,params = [],{}
    for filename in os.listdir(filepath):
        soe.append("data/assimilatefile_{}".format(i))
        params.update({"assimilatefile_{}".format(i):dict(filename=filename,filepath=filepath)})
        i += 1
        if i % 100 == 0 or i == len(os.listdir(filepath)):
            experiment = dict(soe=soe,params=params,meta=dict(substrate="kadi",ma="kadi"))
            requests.post("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'] ,13380 ,"orchestrator" ,"addExperiment"),params= dict(experiment=json.dumps(experiment)))
            soe = []
            params = {}
        if i == 100:
            requests.post("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'] ,13380 ,"orchestrator" ,"infiniteLoop"),params= None)