config = {}

config['servers'] = {
    'psdDriver': {'host': "127.0.0.1", 'port': 13370},
    'psd': {'host': "127.0.0.1", 'port': 13371},
    'palmsensDriver': {'host': "127.0.0.1", 'port': 13374},
    'palmsens': {'host': "127.0.0.1", 'port': 13375},
    'forceDriver': {'host': "127.0.0.1", 'port': 13352},
    'force': {'host': "127.0.0.1", 'port': 13353},
    'orchestrator': {'host': "127.0.0.1", 'port': 13390},
    'dobotDriver': {'host': "127.0.0.1", 'port': 13382},
    'dobot': {'host': "127.0.0.1", 'port': 13391},
    'analysis': {'host': "127.0.0.1", 'port': 13389},
    'measure': {'host': "127.0.0.1", 'port': 13399},
    'ml': {'host': "127.0.0.1", 'port': 13363}
}

config['analysis'] = {'url': "http://127.0.0.1:13368"}
config['ml'] = {'url': "http://127.0.0.1:13362"}
config['measure'] = {'url': "http://127.0.0.1:13398"}

config['palmsensDriver'] = {
    'PalmsensSDK_python': r"C:\Users\juliu\Documents\PSPythonSDK",
    'savepath_raw': r"C:\Users\juliu\helao-dev\temp\palmsens_data",
    'log_folder': r"C:\Users\juliu\helao-dev\temp\palmsens_data\log"
}

config['palmsens'] = {
    'url': "http://127.0.0.1:13374",
    'path_json': r"C:\Users\juliu\helao-dev\temp\palmsens_data"
}

config['dobotDriver'] = {
    'api_path': r"C:\Users\juliu\Documents\RobotRecording\include",
    'ip': "192.168.1.6",
    'dashboard_port': 29999,
    'move_port': 30003,
    'error_codes': r"C:\Users\juliu\Documents\RobotRecording\data\error_codes.json",
    'number_of_joints': 4,
    'end_effector': 2,
    'end_effector_pins': {
        'power': 5,
        'direction': 10
    },
    'end_effector_state': 1,
    'joint_acceleration': 3,
    'linear_acceleration': 3,
    'joint_bounds': [[-80, 80], [-125, 125], [95, 245], [-355, 355]]
}

config['dobot'] = {
    'url': "http://127.0.0.1:13382",
    'safe_home_pose': [371.2, -2.5, 140, 327.5],
    'safe_waste_pose': [355.0, -2.5, 112.0, 327.5],
    'safe_sample_pose': [271.3, -27.8, 115, 327.5],
    'remove_drop_pose': [371.2, -2.5, 108.25, 327.5],
    'forceurl': "http://127.0.0.1:13353"
}

config['forceDriver'] = {'com_port': 5}
config['force'] = {'url': "http://127.0.0.1:13352"}

config['psdDriver'] = {'port': 6, 'baud': 9600, 'psd_type': '4', 'psd_syringe': '1.25m', 'speed': 10} #PSD.PSDTypes.psd4.value, PSD.SyringeTypes.syringe125mL.value

config['psd'] = {
    'url': "http://127.0.0.1:13370",
    'valve': {'S1': 2, 'S2': 3, 'S3': 4, 'S4': 5, 'S5': 6, 'S6': 7, 'Out': 1, 'Mix': 8},
    'volume': 1250,
    'speed': 10
} 

config['orchestrator'] = {'path': r'C:\Users\juliu\data', 'kadiurl': "http://127.0.0.1:13377"}

config['palmsens_visualizer'] = {'orchestrator_url': "http://127.0.0.1:13390", 'socket_url': "ws://127.0.0.1:13374/ws"}

config['analysis'] = {'cp': {'counter_voltage': 4.7},
                      'ocp': {'analysis_points': 10},
                      'eis': {'circuit_list': [
                                            "R_0-p(R_1,CPE_1)-CPE_2",
                                            "R_0-p(R_1,CPE_1)-p(R_2,CPE_2)-CPE_3",
                                            "R_0-p(R_1-W_1,CPE_1)",
                                            "R_0-p(R_1,CPE_1)-p(R_2-W_1,CPE_2)",
                                            "R_0-p(R_1,CPE_1)-p(R_2,CPE_2)-p(R_3-W_1,CPE_3)"
                                            ],
                              'guess_list': [
                                            ["R0", "R1", 1e-10, 0.99, 1e-7, 0.8],
                                            ["R0", "R1", 1e-11,0.98, "R2", 4e-7,0.85, 1e-6,0.9],
                                            ["R0", "R1", 1e+5, 1e-6,0.9],
                                            ["R0", "R1", 1e-10,0.98, "R2", 1e+5, 1e-6,0.9],
                                            ["R0", "R1", 1e-10,0.98, "R2", 1e-10,0.98, "R3", 1e+5, 1e-6,0.9]
                                            ],
                              'bounds_list': [
                                            (("R0", "R1", 1e-13, 0.001, 1e-13, 0),("R0", "R1", 1e-5, 0.999, 1e-3, 1)),
                                            (("R0", "R1", 1e-13,0.001, "R2", 1e-13,0.001, 1e-13,0.001),("R0", "R1", 1e-8,1, "R2", 1e-4,1, 1,1)),
                                            (("R0", "R1", 1e-1, 1e-13,0.001),("R0", "R1", 1e+10, 1,1)),
                                            (("R0", "R1", 1e-13,0.001, "R2",1e-1, 1e-13,0.001),("R0", "R1", 1e-6,1, "R2",1e+10, 1,1)),
                                            (("R0", "R1", 1e-13,0.001, "R2", 1e-13,0.001, "R3",1e-1, 1e-13,0.001),("R0", "R1", 1e-6,1, "R2", 1e-6,1, "R3",1e+10, 1,1))
                                            ],
                              'semicircles_max': 3,
                              'metric': 'chi2',
                              'save_path': r'C:\Users\juliu\data\Documents\EIS'}
                    }

config['launch'] = {
    'server': ['dobotDriver', 'forceDriver', 'palmsensDriver', 'psdDriver'],
    'action': ['dobot', 'force', 'palmsens', 'psd', 'analysis', 'measure', 'ml'],
    'orchestrator': ['orchestrator'],
    'visualizer': ['palmsens_visualizer'],
    'process': []}

config['instrument'] = "sdc"