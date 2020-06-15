# default universal (non-instrument specific) config parameters can be placed here but need to override with the specific config
GALIL_SETUPD = {
    "count_to_mm": {
        "A": 1.0 / 3154.787,
        "B": 1.0 / (6395.45),
        "C": 1.0 / (6395.45),
        "D": 1.0 / (6397.95),
        "u": 154.1133 / 985482.0,
    },
    "galil_ip_str": "192.168.200.23",
    "def_speed_count_sec": 10000,
    "max_speed_count_sec": 25000,
    "ipstr": "192.168.200.23",
    "axis_id": {"x": "D", "y": "B", "z": "C", "s": "A", "t": "E", "u": "F"},
    "axlett": "ABCD",
}
GALIL_SIMULATE = True

GAMRY_SETUPD = {
    "path_to_gamrycom": r"C:\Program Files (x86)\Gamry Instruments\Framework\GamryCOM.exe",
    "temp_dump": r"C:\Users\hte\Documents\lab_automation\temp",
}

FASTAPI_HOST = "127.0.0.1"
MOTION_PORT = 8001
ECHEM_PORT = 8003

if __package__:
    from .config_edep import *  # this is the only place where the instrument-specif config is specified
else:
    from config_edep import *

# TODO: figure out how to pass the namespace of config_edp to all the py that import config.py


# specify here if there is file from simulate folder that will be used by drivers to customize the simulated experiment
