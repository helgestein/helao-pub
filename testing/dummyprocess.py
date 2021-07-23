import requests
import sys
sys.path.append("config")
from jackspc_config import config
import json

if __name__ == "__main__":
    soe = ["orchestrator/start","dummy:1/lmao_0"]
    for i in range(9):
        soe += [f"orchestrator/wait_{i}",f"orchestrator/modify_{i}",f"dummy:1/lmao_{i+1}"]
    soe += ["orchestrator/finish"]
    params = {'start':{'collectionkey':'dummytest1'},'finish':None}
    params.update({"lmao_0":{'t':5}})
    params.update({f"lmao_{i}":{'t':'?'} for i in range(1,10)})
    params.update({f"wait_{i}":{'addresses':f"experiment_0:3/fakeml_{i}"} for i in range(9)})
    params.update({f"modify_{i}":{'addresses':f'experiment_0:3/fakeml_{i}/data/data/val1','pointers':f'lmao_{i+1}/t'} for i in range(9)})
    meta = {}
    experiment = dict(soe=soe,params=params,meta=meta)
    requests.post(f"http://{config['servers']['orchestrator']['host']}:{config['servers']['orchestrator']['port']}/orchestrator/addExperiment",params= dict(experiment=json.dumps(experiment),thread=1))
    
    soe = ["dummy:1/lmao_0"]
    for i in range(9):
        soe += [f"orchestrator/wait_{i}",f"orchestrator/modify_{i}",f"dummy:1/lmao_{i+1}"]
    soe += ["orchestrator/finish"]
    params = {'finish':None}
    params.update({"lmao_0":{'t':5}})
    params.update({f"lmao_{i}":{'t':'?'} for i in range(1,10)})
    params.update({f"wait_{i}":{'addresses':f"experiment_0:3/fakeml_{i}"} for i in range(9)})
    params.update({f"modify_{i}":{'addresses':f'experiment_0:3/fakeml_{i}/data/data/val2','pointers':f'lmao_{i+1}/t'} for i in range(9)})
    meta = {}
    experiment = dict(soe=soe,params=params,meta=meta)
    requests.post(f"http://{config['servers']['orchestrator']['host']}:{config['servers']['orchestrator']['port']}/orchestrator/addExperiment",params= dict(experiment=json.dumps(experiment),thread=2))

    soe = []
    for i in range(9):
        soe += [f"orchestrator/wait_{i}",f"dummy:1/fakeml_{i}"]
    soe += ["orchestrator/finish"]
    params = {'finish':None}
    params.update({f"fakeml_{i}":None for i in range(9)})
    params.update({f"wait_{i}":{'addresses':[f"experiment_0:1/lmao_{i}",f"experiment_0:2/lmao_{i}"]} for i in range(9)})
    meta = {}
    experiment = dict(soe=soe,params=params,meta=meta)
    requests.post(f"http://{config['servers']['orchestrator']['host']}:{config['servers']['orchestrator']['port']}/orchestrator/addExperiment",params= dict(experiment=json.dumps(experiment),thread=3))









