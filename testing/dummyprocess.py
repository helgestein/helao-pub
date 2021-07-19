import requests
import sys
sys.path.append("config")
from jackspc_config import config
import json

if __name__ == "__main__":
    soe = ["orchestrator/start"]
    for i in range(10):
        soe += [f"dummy:1/lmao_{i}",f"orchestrator/wait_{i}"]
    soe += ["orchestrator/finish"]
    params = {'start':{'collectionkey':'dummytest1'},'finish':None}
    params.update({f"lmao_{i}":{'t':5} for i in range(10)})
    params.update({f"wait_{i}":{'addresses':f"experiment0:2/lmao_{i}"} for i in range(10)})
    meta = {}
    experiment = dict(soe=soe,params=params,meta=meta)
    requests.post(f"http://{config['servers']['orchestrator']['host']}:{config['servers']['orchestrator']['port']}/orchestrator/addExperiment",params= dict(experiment=json.dumps(experiment),thread=1))
    
    soe = []
    for i in range(10):
        soe += [f"dummy:1/lmao_{i}","orchestrator/wait"]
    soe += ["orchestrator/finish"]
    params = {'finish':None}
    params.update({f"lmao_{i}":{'t':10} for i in range(10)})
    params.update({f"wait_{i}":{'addresses':f"experiment0:1/lmao_{i}"} for i in range(10)})
    meta = {}
    experiment = dict(soe=soe,params=params,meta=meta)
    requests.post(f"http://{config['servers']['orchestrator']['host']}:{config['servers']['orchestrator']['port']}/orchestrator/addExperiment",params= dict(experiment=json.dumps(experiment),thread=2))