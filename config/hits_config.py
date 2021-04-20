config = dict()

config['servers'] = dict(kadiServer = dict(host="127.0.0.1", port=13376),
                         dataServer = dict(host="127.0.0.1", port=13377),
                         orchestrator = dict(host= "127.0.0.1", port= 13380),
                         oceanServer = dict(host= "127.0.0.1", port= 13383),
                         ramanServer = dict(host= "127.0.0.1", port= 13384),
                         arcoptixServer = dict(host= "127.0.0.1", port= 13385),
                         ftirServer = dict(host= "127.0.0.1", port= 13386),
                         owisServer = dict(host= "127.0.0.1", port= 13387),
                         tableServer = dict(host= "127.0.0.1", port= 13388))

config['kadi'] = dict(host = r"https://polis-kadi4mat.iam-cms.kit.edu",
            PAT = r"78ac200f0379afb4873c7b0ee71f5489946158fe882466a9",group='2')

#r'C:\Program Files\ARCoptix\ARCspectro Rocket 2.4.9.13 - x64\ARCsoft.ARCspectroMd'
#i don't know why a relative path is needed in scripts. it is not in terminal. but here we are.
config['arcoptix'] = dict(dll = r'..\..\..\..\..\Program Files\ARCoptix\ARCspectro Rocket 2.4.9.13 - x64\ARCsoft.ARCspectroMd')

config['orchestrator'] = dict(path=r'C:\Users\LaborRatte23-3\Documents\data')

config['owis'] = dict(serials=[dict(port='COM4', baud=9600, timeout=0.1),dict(port='COM6', baud=9600, timeout=0.1),
                                dict(port='COM9', baud=9600, timeout=0.1),dict(port='COM10', baud=9600, timeout=0.1)],
                                coordinates=[None,None,(),()],roles=['x','y','ftir','raman'],
                                currents=[dict(mode=0,drive=40,hold=60),dict(mode=0,drive=50,hold=30),dict(mode=0,drive=50,hold=50),dict(mode=0,drive=50,hold=50)],
                                safe_positions=[None,None,300000,300000])

config['launch'] = dict(server = ['owis_server','ocean_server','arcoptix_server','kadi_server'],
                        action = ['owis_action','raman_ocean','ftir_arcoptix','kadi_action'],
                        orchestrator = ['mischbares'],
                        visualizer = ['hits_visualizer'],
                        process = [])
