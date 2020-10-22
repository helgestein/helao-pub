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

#check if home, check if stage is aligned, check optimal probe height, for each sample:[move sample into position, move probe to optimal measuring point, measure, move probe to home
#0,80 is where we are at now for the origin i think?
grid = [(i,j) for i in range(0,100,10) for j in range(0,100,10)]




if __name__ == "__main__":
    task = "make"
    if task == "test":
        mm.zeroj = [-90, 0, 0, 0, 0, 120]
        mm.url = "http://{}:{}".format(config['servers']['mecademicServer']['host'], config['servers']['mecademicServer']['port'])
        oa.url = "http://{}:{}".format(config['servers']['owisServer']['host'], config['servers']['owisServer']['port'])
        mm.move_to_home()
        oa.configure(0)
        oa.configure(1)
        for loc in grid:
            oa.move(loc)
            mm.bring_raman()
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
            soe.append("movement/bringRaman_{}".format(i))
            params.update({"bringRaman_{}".format(i):None})
            soe.append("oceanAction/read_{}".format(i))
            params.update({"read_{}".format(i):dict(filename="C:/Users/Operator/Documents/temp/dry_dry_"+str(i))})
            soe.append("movement/moveToHome_{}".format(i+1))
            params.update({"moveToHome_{}".format(i+1):None})
            i += 1
        experiment = dict(soe=soe,params=params,meta=dict(substrate="dry",ma="dry"))
        #experiment = dict(soe=["movement/moveToHome_0"],params=dict(moveToHome_0=None),meta=dict(substrate="dry",ma="dry"))
        requests.post("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'] ,13380 ,"orchestrator" ,"addExperiment"),params= dict(experiment=json.dumps(experiment)))
        requests.post("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'] ,13380 ,"orchestrator" ,"infiniteLoop"),params= None)

