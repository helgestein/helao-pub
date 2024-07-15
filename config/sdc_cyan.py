config = dict()

config['servers'] = dict(psdDriver=dict(host="127.0.0.1", port=13370),
                         psd=dict(host="127.0.0.1", port=13371),
                         palmsensDriver=dict(host="127.0.0.1", port=13374),
                         palmsens=dict(host="127.0.0.1", port=13375),
                         forceDriver=dict(host="127.0.0.1", port=13352),
                         force=dict(host="127.0.0.1", port=13353),
                         orchestrator=dict(host="127.0.0.1", port=13390),
                         dobotDriver=dict(host="127.0.0.1", port=13382),
                         dobot=dict(host="127.0.0.1", port=13391),
                         analysis=dict(host="127.0.0.1", port=13389),
                         measure=dict(host="127.0.0.1", port=13399),
                         ml=dict(host="127.0.0.1", port=13363))

#config['measure:1'] = dict(url="http://192.168.31.123:6667")
#config['measure:2'] = dict(url="http://192.168.31.114:6669")
config['analysis'] = dict(url="http://127.0.0.1:13368")
config['ml'] = dict(url="http://127.0.0.1:13362")
config['measure'] = dict(url="http://127.0.0.1:13398")

config['palmsensDriver'] = dict(PalmsensSDK_python = r"C:\Users\juliu\Documents\PSPythonSDK",
                                savepath_raw = r"C:\Users\juliu\helao-dev\temp\palmsens_data",
                                log_folder = r"C:\Users\juliu\helao-dev\temp\palmsens_data\log")

config['palmsens'] = dict(url="http://127.0.0.1:13374")

config['dobotDriver'] = {
    "api_path": r"C:\Users\juliu\Documents\RobotRecording\include",
    "ip": "192.168.1.6",
    "dashboard_port": 29999,
    "move_port": 30003,
    "error_codes": r"C:\Users\juliu\Documents\RobotRecording\data\error_codes.json",
    "number_of_joints": 4,
    "end_effector": 2,
    "end_effector_pins": {
        "power":5,
        "direction": 10},
    "end_effector_state": 1,
    "joint_acceleration": 3,
    "linear_acceleration": 3,
    "joint_bounds": [[-80, 80], [-125, 125], [95, 245], [-355, 355]] 
}

config["dobot"] = {
    "url": "http://127.0.0.1:13382",
    "safe_home_pose": [371.2, -2.5, 140, 327.5],
    "safe_waste_pose": [355.0, -2.5, 112.0, 327.5],
    "safe_sample_pose": [271.3, -27.8, 115, 327.5],
    "remove_drop_pose": [371.2, -2.5, 108.25, 327.5],
    "forceurl":"http://127.0.0.1:13353"
}

config['forceDriver'] = dict(com_port=5)
config['force'] = dict(url="http://127.0.0.1:13352")

config['psdDriver'] = dict(port=6, baud=9600, psd_type = '4', psd_syringe = '1.25m', speed = 10) #PSD.PSDTypes.psd4.value, PSD.SyringeTypes.syringe125mL.value

config['psd'] = dict(url="http://127.0.0.1:13370", valve = {'S1': 2, 'S2': 3, 'S3': 4, 'S4': 5, 'S5': 6, 'S6': 7, 'Out': 1, 'Mix': 8}, volume = 1250, speed = 10) # volume of the pump corresponds to the type, input in µL
config['orchestrator'] = dict(path=r'C:\Users\juliu\data', kadiurl="http://127.0.0.1:13377")

config['launch'] = dict(server=['dobotDriver', 'forceDriver', 'palmsensDriver', 'psdDriver'],
                        action=['dobot', 'force', 'palmsens', 'psd', 'analysis', 'measure', 'ml'],
                        orchestrator=['orchestrator'],
                        visualizer=[],
                        process=['plot_process'])

config['instrument'] = "sdc"