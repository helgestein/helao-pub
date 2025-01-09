import os
import sys
import json
import requests
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(helao_root)
from util import makeGrid



if __name__ == "__main__":
    grid = makeGrid(10,10,50,32.3)
    print(grid)
    print(len(grid))
    soe = ["orchestrator/start"]
    params = {"start":{"collectionkey":"ramandisctest"}}
    meta = {}
    requests.post("http://127.0.0.1:13380/orchestrator/addExperiment",
                  params={"experiment":json.dumps({"soe":soe,"params":params,"meta":meta})}).json()
    for p in grid:
        soe = ["owis/moveprobe_0","owis/movetable","owis/moveprobe_1"]
        params = {"moveprobe_0":{"z":10,"probe":"raman","sample":"sem"},
                  "movetable":{"pos":json.dumps(p.tolist()),"probe":"raman","sample":"sem"},
                  "moveprobe_1":{"z":2,"probe":"raman","sample":"sem"}}
        requests.post("http://127.0.0.1:13380/orchestrator/addExperiment",
                      params={"experiment":json.dumps({"soe":soe,"params":params,"meta":meta})}).json()
    soe = ["orchestrator/finish"]
    params = {"finish":None}
    requests.post("http://127.0.0.1:13380/orchestrator/addExperiment",
                  params={"experiment":json.dumps({"soe":soe,"params":params,"meta":meta})}).json()
