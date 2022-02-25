config = dict()

config['servers'] = {'dummy': dict(host="127.0.0.1",port=6669), 'orchestrator' : dict(host="127.0.0.1",port=13380)}




config['dummy'] = dict()

config['orchestrator'] = dict(path='C:/Users/Operator/Documents/data',kadiurl="http://127.0.0.1:13377")


config['launch'] = dict(server = [],
                        action = ['dummy'],
                        orchestrator = ['orchestrator'],
                        visualizer = [],
                        process = [])

config['instrument'] = "labpc"