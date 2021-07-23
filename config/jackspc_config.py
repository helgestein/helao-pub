config = dict()

config['servers'] = {'dummy:1': dict(host="127.0.0.1",port=6669), 'orchestrator' : dict(host="127.0.0.1",port=13380)}

config['servers'].update(dict(measure=dict(host="127.0.0.1", port=13368),
                         analysis=dict(host="127.0.0.1", port=13369),
                         ml=dict(host="127.0.0.1", port=13363)))

config['measure'] = dict(url="http://127.0.0.1:13368")
config['analysis'] = dict(url="http://127.0.0.1:13369")
config['ml'] = dict(url="http://127.0.0.1:13363")




config['dummy:1'] = dict()

config['orchestrator'] = dict(path='C:/Users/jkflowers/Documents/data',kadiurl="http://127.0.0.1:13377")


config['launch'] = dict(server = [],
                        action = ['dummy:1','measure','analysis','ml'],
                        orchestrator = ['orchestrator'],
                        visualizer = [],
                        process = [])

config['instrument'] = "jackspc"