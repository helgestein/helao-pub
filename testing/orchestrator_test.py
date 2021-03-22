import requests
import sys
sys.path.append("../config")
from mischbares_small import config
import json



l = 5
n = 5
experiment = dict(soe=["orchestrator/start"],params={"start":None},meta=dict(substrate=0,ma=[0,0],r=.01))
requests.post("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'] ,13380 ,"orchestrator" ,"addExperiment"),params= dict(experiment=json.dumps(experiment)))
for i in range(l):

    experiment = dict(soe=["orchestrator/dummy" for j in range(n)],params={"dummy":None},meta=dict(substrate=0,ma=[i,0],r=.01))
    requests.post("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'] ,13380 ,"orchestrator" ,"addExperiment"),params= dict(experiment=json.dumps(experiment)))
experiment = dict(soe=["orchestrator/finish"],params={"finish":None},meta=dict(substrate=0,ma=[0,0],r=.01))
requests.post("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'] ,13380 ,"orchestrator" ,"addExperiment"),params= dict(experiment=json.dumps(experiment)))
