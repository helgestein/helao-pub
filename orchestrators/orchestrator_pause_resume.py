import requests
import sys
sys.path.append(r'../config')
sys.path.append('config')
from sdc_4 import config

def orchestrator_test(action,thread=0):
    server = 'orchestrator'
    action = action
    params = dict(thread=thread)
    print("requesting")
    print(requests.post("http://{}:{}/{}/{}".format(
        config['servers']['orchestrator']['host'],config['servers']['orchestrator']['port'], server, action), params=params).json())

orchestrator_test('pause', thread=0)
orchestrator_test('resume', thread=0)
orchestrator_test('clear', thread=0)
orchestrator_test('kill', thread=0)
orchestrator_test('getStatus', thread=0)

requests.post("http://127.0.0.1:13390/orchestrator/pause",params=dict(thread=0))
requests.post("http://127.0.0.1:13390/orchestrator/resume",params=dict(thread=0))