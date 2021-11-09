from math import pi

config = dict()

config['servers'] = dict(kadiDriver = dict(host="127.0.0.1",port=13376),
                         kadi = dict(host="127.0.0.1",port=13377),
                         orchestrator = dict(host="127.0.0.1",port=13380),
                         oceanDriver = dict(host="127.0.0.1",port=13383),
                         ocean = dict(host="127.0.0.1",port=13384),
                         arcoptixDriver = dict(host="127.0.0.1",port=13385),
                         arcoptix = dict(host="127.0.0.1",port=13386),
                         owisDriver = dict(host="127.0.0.1",port=13387),
                         owis = dict(host="127.0.0.1",port=13388))

config['kadiDriver'] = dict(host = "https://polis-kadi4mat.iam-cms.kit.edu",
            PAT = "99804736e3c4a1059eb5f805dc1520dab6f8714f6c7d2d88")
config['kadi'] = dict(group='2',url="http://127.0.0.1:13376")

#r'C:\Program Files\ARCoptix\ARCspectro Rocket 2.4.9.13 - x64\ARCsoft.ARCspectroMd'
#i don't know why a relative path is needed in scripts. it is not in terminal. but here we are.
config['arcoptixDriver'] = dict(dll = r'..\..\..\..\..\Program Files\ARCoptix\ARCspectro Rocket 2.4.9.13 - x64\ARCsoft.ARCspectroMd',safepath = 'C:/Users/Operator/Documents/data/safe/ftir')
config['arcoptix'] = dict(url="http://127.0.0.1:13385")

config['orchestrator'] = dict(path=r'C:\Users\Operator\Documents\data',kadiurl="http://127.0.0.1:13377")

config['owisDriver'] = dict(serials=[dict(port='COM4', baud=9600, timeout=0.1),dict(port='COM11', baud=9600, timeout=0.1),
                                dict(port='COM13', baud=9600, timeout=0.1)],
                                currents=[dict(mode=1,drive=80,hold=40),dict(mode=0,drive=50,hold=30),dict(mode=0,drive=50,hold=50)],
                                safe_positions=[1500000,None,600000])
config['owis'] = dict(coordinates=[None,None,
                        {"sem":{"x":68,"y":91,"theta":pi,"I":True,"z":10.5},"fto":{"x":0,"y":0,"theta":0,"I":True,"z":0},"oneoff":{"x":0,"y":0,"theta":0,"I":True,"z":0}}],
                        roles=['x','y','raman'],url="http://127.0.0.1:13387",ramanurl="http://127.0.0.1:13383")
#let v1 be vector of x-y in motor coordinates, v2 vector of x-y in sample coordinates.
#v2 = R(theta)I(v1-[x,y]), so v1 = IR(-theta)v2 + [x,y]
#R is 2x2 rotation matrix, and I is identity matrix if I=True, and inversion on x if I=False.
#z is coordinates of probe motor when probe resting on sample

config['oceanDriver'] = dict(safepath = 'C:/Users/Operator/Documents/data/safe/raman')
config['ocean'] = dict(url="http://127.0.0.1:13383")

#still need to fix launch and visualizer
config['launch'] = dict(server = ['owisDriver','oceanDriver','arcoptixDriver','kadiDriver'],
                        action = ['owis','ocean','arcoptix','kadi'],
                        orchestrator = ['mischbares'])

config['instrument'] = "hits"


#so i am relieved that the turbulence wasn't forcasted; i couldn't have changed anyways