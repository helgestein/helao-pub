import requests 
from config.sdc_cyan import config 
def test_fnc(action, params): 
   server = 'dobot' 
   action = action 
   params = params 
   r = requests.get('http://{}:{}/{}/{}'.format(config['servers']['dobot']['host'], config['servers']['dobot']['port'], server, action), params= params).json() 
   print(r) 
