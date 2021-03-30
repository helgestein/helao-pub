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

config['arcoptix'] = dict(dll = r'..\..\..\arcoptix\API\Rocket_2_4_9_LabVIEWDrivers\200-LabVIEWDrivers\ARCsoft.ARCspectroMd')

config['orchestrator'] = dict(path=r'C:\Users\LaborRatte23-3\Documents\data')

config['owis'] = dict(serials=[dict(port='COM4', baud=9600, timeout=0.1),dict(port='COM6', baud=9600, timeout=0.1)])

config['launch'] = dict(server = ['owis_server','ocean_server','arcoptix_server','kadi_server'],
                        action = ['owis_action','raman_ocean','ftir_arcoptix','kadi_action'],
                        orchestrator = ['mischbares'],
                        visualizer = ['raman_visualizer'],
                        process = ['testing/testing_raman_stage'])

