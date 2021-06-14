import sys
sys.path.append("../config")
sys.path.append("config")
import time
import json
from fastapi import FastAPI,BackgroundTasks
import requests
import numpy
from sklearn.decomposition import NMF
from hits_config import config

def hits_points(points):
    #soe = ["orchestrator/start","table/calibration"]
    #params = {"start":None,"calibration":dict(x=json.dumps([70,10]),m=json.dumps([70,20]),y=json.dumps([10,20]),d=2)}
    soe = ["orchestrator/start"]
    params = {"start":None}
    meta = dict(substrate=1,ma=[0,0],r=.00001)
    experiment = dict(soe=soe,params=params,meta=meta)
    requests.post("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'] ,13380 ,"orchestrator" ,"addExperiment"),params= dict(experiment=json.dumps(experiment)))
    for i in range(len(points)):
        time.sleep(.01)
        #soe = [f"table/movetable_{i}",f"table/sampleheight_{i}",f"oceanAction/read_{i}"]
        #params = {f"movetable_{i}":dict(pos=json.dumps(points[i]),key="raman"),f"sampleheight_{i}":dict(pos=json.dumps(points[i]),f=5,probe="raman"),f"read_{i}":dict(t=10000000,filename=f"ramanmeasure{int(time.time())}_{i}.json")}
        soe = [f"table/movetable_{i}",f"oceanAction/read_{i}"]
        params = {f"movetable_{i}":dict(pos=json.dumps(points[i]),key="raman"),f"read_{i}":dict(t=10000000,filename=f"ramanmeasure{int(time.time())}_{i}.json")}
        meta = dict(substrate=1,ma=points[i],r=.00001)
        if i == len(points) - 1:
            soe.append("orchestrator/finish")
            params.update({"finish":None})
        experiment = dict(soe=soe,params=params,meta=meta)
        requests.post("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'] ,13380 ,"orchestrator" ,"addExperiment"),params= dict(experiment=json.dumps(experiment)))

if __name__ == "__main__":
    #points = [[i,j] for i in numpy.linspace(3,75,145) for j in numpy.linspace(5,27,45)]
    points = [[i,j] for i in numpy.linspace(2,22,201) for j in numpy.linspace(4,24,201)]
    #points = [[19,19],[20,20]]
    #hits_points(points[16261:])
    hits_points(points[16229:])
    #points2 = [[i,j] for i in numpy.linspace(10,20,101) for j in numpy.linspace(10,20,101)]
    #hits_points(points2[:10])
    #soe = ["orchestrator/start","table/calibration_1","table/calibration_2","table/calibration_3","table/calibration_4","table/calibration_5"]
    #params = {"start":None,"calibration_1":dict(x=json.dumps([20,5]),m=json.dumps([5,5]),y=json.dumps([5,20]),d=2),
    #            "calibration_2":dict(x=json.dumps([20,5]),m=json.dumps([5,5]),y=json.dumps([5,20]),d=2),
    #            "calibration_3":dict(x=json.dumps([20,5]),m=json.dumps([5,5]),y=json.dumps([5,20]),d=2),
    #            "calibration_4":dict(x=json.dumps([20,5]),m=json.dumps([5,5]),y=json.dumps([5,20]),d=2),
    #            "calibration_5":dict(x=json.dumps([20,5]),m=json.dumps([5,5]),y=json.dumps([5,20]),d=2)}
    #meta = dict(substrate=1,ma=[0,0],r=.00001)
    
    #experiment = dict(soe=soe,params=params,meta=meta)
    #requests.post("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'] ,13380 ,"orchestrator" ,"addExperiment"),params= dict(experiment=json.dumps(experiment)))

