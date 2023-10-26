config = dict()

#urls of all servers
config['servers'] = dict(orchestrator = dict(host="192.168.31.114",port=13380),
                         templateDriver = dict(host="127.0.0.1",port=13385),
                         template = dict(host="127.0.0.1",port=13386))

#config information for action and driver servers
config['templateDriver'] = dict()
config['template'] = dict(url="http://127.0.0.1:13385")


#path determines the directory under which h5 data files will be saved
config['orchestrator'] = dict(path=r'C:\Users\Operator\Documents\data',kadiurl=None)

#
config['launch'] = dict(server = ['templateDriver'],
                        action = ['template'],
                        orchestrator = ['orchestrator'])

config['instrument'] = "template"

