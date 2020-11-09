import sys
sys.path.append("../action")
sys.path.append("../config")
sys.path.append("../orchestrators")
from mischbares_small import config
import movement_mecademic as mm
import owis_action as oa
import time
import mischbares
import json
from fastapi import FastAPI,BackgroundTasks
import requests
import numpy as np
#check if home, check if stage is aligned, check optimal probe height, for each sample:[move sample into position, move probe to optimal measuring point, measure, move probe to home
#0,80 is where we are at now for the origin i think?
x, y = np.meshgrid([2.5 * i for i in range(27)], [2.5 * i for i in range(8)])
x, y = x.flatten(), y.flatten()
grid = [[x[i]+5,y[i]+10] for i in range(len(x))]

#motor 0 count increases as y increases
#motor 1 count increases as x decreases

grid = [[46.6+i[1],79.4-i[0]] for i in grid]



if __name__ == "__main__":
    print(str(grid))
    task = "make"
    if task == "test":
        mm.url = "http://{}:{}".format(config['servers']['mecademicServer']['host'], config['servers']['mecademicServer']['port'])
        oa.url = "http://{}:{}".format(config['servers']['owisServer']['host'], config['servers']['owisServer']['port'])
        mm.move_to_home()
        oa.configure(0)
        oa.configure(1)
        for loc in grid:
            oa.move(json.dumps(loc))
            mm.safeRaman()
            mm.move_to_home()
    if task == "make":
        soe = []
        params = {}
        soe.append("movement/moveToHome_0")
        params.update({"moveToHome_0":None})
        soe.append("table/configure_0")
        params.update({"configure_0":dict(motor=0)})
        soe.append("table/configure_1")
        params.update({"configure_1":dict(motor=1)})
        i = 0
        for loc in grid:
            soe.append("table/move_{}".format(i))
            params.update({"move_{}".format(i):dict(loc=json.dumps(loc))})
            soe.append("movement/measuringRaman_{}".format(i))
            params.update({"measuringRaman_{}".format(i):dict(z=5,h=0)})
            soe.append("oceanAction/read_{}".format(i))
            params.update({"read_{}".format(i):dict(t=10000000,filename="C:/Users/Operator/Documents/temp/dry_dry_"+str(i))})
            soe.append("movement/safeRaman_{}".format(i+1))
            params.update({"safeRaman_{}".format(i+1):None})
            i += 1
        experiment = dict(soe=soe,params=params,meta=dict(substrate="coppertape1",ma="lmao"))
        #experiment = dict(soe=["movement/moveToHome_0"],params=dict(moveToHome_0=None),meta=dict(substrate="dry",ma="dry"))
        requests.post("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'] ,13380 ,"orchestrator" ,"addExperiment"),params= dict(experiment=json.dumps(experiment)))
        requests.post("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'] ,13380 ,"orchestrator" ,"infiniteLoop"),params= None)

