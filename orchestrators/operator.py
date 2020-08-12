import requests
import sys
import json
sys.path.append('../config')
 # this does not exit
from mischbares_small import config

url = "http://{}:{}".format(config['servers']['orchestrator']['host'],config['servers']['orchestrator']['port'])

#start the infinite loop
res = requests.post("{}/orchestrator/infiniteLoop".format(url)).json()

#get the position from lang

a = dict(soe=['motor/getPos_0'], params = dict(getPos_0 = None))
res = requests.post("{}/orchestrator/addExperiment".format(url),params={'experiment':json.dumps(a)}).json()

a = dict(soe=['motor/moveRel_0'], params = dict(moveRel_0 = {'dx': 10, 'dy': 10, 'dz': 10}))
res = requests.post("{}/orchestrator/addExperiment".format(url),params={'experiment':json.dumps(a)}).json()


