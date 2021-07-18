import requests
import sys
sys.path.append("config")
from jackspc_config import config
import json

if __name__ == "__main__":
    soe = ["orchestrator/start"]+[f"dummy:1/lmao_{i}" for i in range(10)]+["orchestrator/finish"]
    params = {'start':{'collectionkey':'dummytest1'},'finish':None}
    params.update({f"lmao_{i}":{'t':i} for i in range(10)})
    meta = {}
    experiment = dict(soe=soe,params=params,meta=meta)
    requests.post(f"http://{config['servers']['orchestrator']['host']}:{config['servers']['orchestrator']['port']}/orchestrator/addExperiment",params= dict(experiment=json.dumps(experiment)))