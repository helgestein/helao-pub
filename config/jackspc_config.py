config = dict()

config['servers'] = {'oceanDriver': dict(host="127.0.0.1",port=6669), 'ocean': dict(host="127.0.0.1",port=6670), 'orchestrator' : dict(host="127.0.0.1",port=13380)}


config['oceanDriver'] = dict(safepath = 'C:/Users/jkflowers/Documents')

config['ocean'] = dict(wavelength=532,url="http://127.0.0.1:6669")

config['orchestrator'] = dict(path='C:/Users/jkflowers/Documents/data',kadiurl="http://127.0.0.1:13377")


config['launch'] = dict(server = ['oceanDriver'],
                        action = ['ocean'],
                        orchestrator = ['orchestrator'],
                        visualizer = [],
                        process = [])

config['instrument'] = "labpc"