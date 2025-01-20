"""
Utility for launching & appending servers to running server group

launch via 'python append.py {running_config_prefix} {append_config_prefix}'

"""

import os
import sys
from importlib import import_module

helao_root = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(helao_root)
from helao_launch import launcher
confPrefix = sys.argv[1]
appendPrefix = sys.argv[2]

def appender(confPrefix, appendPrefix):
    confDict = import_module(f"{confPrefix}").config
    appenDict = import_module(f"{appendPrefix}").config
    overlap = [k for k in appenDict["servers"].keys() if k in confDict["servers"].keys()]
    if overlap:
        print(f"config dict from '{appendPrefix}.py' overlaps with '{confPrefix}.py")
        return None
    else:
        confDict["servers"].update(appenDict["servers"])
        launcher(confPrefix, confDict)


if __name__ == "__main__":
    appender(confPrefix, appendPrefix)
