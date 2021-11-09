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

config['owisDriver'] = dict(serials=[dict(port='COM4', baud=9600, timeout=0.1),dict(port='COM6', baud=9600, timeout=0.1),
                                dict(port='COM9', baud=9600, timeout=0.1),dict(port='COM10', baud=9600, timeout=0.1)],
                                currents=[dict(mode=0,drive=40,hold=60),dict(mode=0,drive=50,hold=30),dict(mode=0,drive=50,hold=50),dict(mode=0,drive=50,hold=50)],
                                safe_positions=[None,None,300000,300000])
config['owis'] = dict(coordinates=[None,None,(),(336.7,36.8,4.5,[[-1,0],[0,1]],True)],roles=['x','y','ftir','raman'],
                      url="http://127.0.0.1:13387",ramanurl="http://127.0.0.1:13383")

config['oceanDriver'] = dict(safepath = 'C:/Users/Operator/Documents/data/safe/raman')
config['ocean'] = dict(url="http://127.0.0.1:13383")

#still need to fix launch and visualizer
config['launch'] = dict(server = ['owisDriver','oceanDriver','arcoptixDriver','kadiDriver'],
                        action = ['owis','ocean','arcoptix','kadi'],
                        orchestrator = ['mischbares'])

config['instrument'] = "hits"


#so i am relieved that the turbulence wasn't forcasted; i couldn't have changed anyways