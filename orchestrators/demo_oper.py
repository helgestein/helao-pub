"""
Simple orchestrator for helao world demo
"""

import os
import sys
import json
import requests
from importlib import import_module

from munch import munchify

helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
config = import_module("world").config
conf = munchify(config)
orchKey = 'orchestrator'
C = conf.servers[orchKey]
url = f"http://{C.host}:{C.port}"

#start the infinite loop
res = requests.get(f"{url}/{orchKey}/infiniteLoop").json()

# move 10.0 mm relative on axis 'x'
act0 = dict(soe=['motor/move'], 
        params=dict(x_mm=10.0,
                    axis='x',
                    speed=None,
                    mode="relative"
                    )
        )
res0 = requests.get(f"{url}/{orchKey}/addExperiment",
                    params={'experiment': json.dumps(act0)}).json()
print(res0)

act1 = dict(soe=['motor/move'],
        params=dict(x_mm=-10.0,
                    axis='y',
                    speed=None,
                    mode="relative"
                    )
        )
res1 = requests.get(f"{url}/{orchKey}/addExperiment",
                    params={'experiment': json.dumps(act1)}).json()
print(res1)


act2 = dict(soe=['potentiostat/potential_cycle'],
            params=dict(Vinit=-0.5,
                        Vfinal=-0.5,
                        Vapex1=0.5,
                        Vapex2=0.5,
                        ScanRate=0.1,
                        Cycles=1,
                        SampleRate=0.004,
                        control_mode="galvanostatic"
                        )
            )
res2 = requests.get(f"{url}/{orchKey}/addExperiment",
                    params={'experiment': json.dumps(act2)}).json()
print(res2)

act3 = dict(soe=['potentiostat/potential_cycle'],
            params=dict(Vinit=0,
                        Vfinal=0,
                        Vapex1=1.0,
                        Vapex2=-1.0,
                        ScanRate=0.2,
                        Cycles=1,
                        SampleRate=0.05,
                        control_mode="galvanostatic"
                        )
            )
res3 = requests.get(f"{url}/{orchKey}/addExperiment",
                    params={'experiment': json.dumps(act3)}).json()
print(act3)
