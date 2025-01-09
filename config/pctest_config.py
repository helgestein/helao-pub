config = dict()

config['servers'] = dict(orchestrator=dict(host="127.0.0.1", port=13380))

config['servers'].update({'measure:2': dict(host="192.168.31.114",port=9001)})
config['servers'].update({'measure:1': dict(host="192.168.31.123",port=6667)})
config['servers'].update({'analysis': dict(host="192.168.31.114",port=6642)})
config['servers'].update({'ml': dict(host="192.168.31.114",port=6612)})

config['measure:2'] = dict(url="http://192.168.31.114:6669")
config['analysis'] = dict(url="http://192.168.31.114:6669")
config['ml'] = dict(url="http://192.168.31.114:6669")

config['orchestrator'] = dict(path=r'C:\Users\Operator\Documents\data',kadiurl="http://127.0.0.1:13377")


config['launch'] = dict(server = [],
                        action = ['measure:2','analysis','ml'],
                        orchestrator = ['orchestrator'],
                        visualizer = [],
                        process = [])

config['instrument'] = "jackspc"