config = dict()

config['servers'] = {'dummy:1': dict(host="127.0.0.1",port=6669), 'orchestrator' : dict(host="127.0.0.1",port=13380)}



config['dummy:1'] = dict()

config['orchestrator'] = dict(path='C:/Users/jkflowers/Documents/data',kadiurl="http://127.0.0.1:13377")


config['launch'] = dict(server = [],
                        action = ['dummy:1'],
                        orchestrator = ['orchestrator'],
                        visualizer = [],
                        process = [])

config['instrument'] = "jackspc"