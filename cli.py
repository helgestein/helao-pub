"""
Command line interface for manual control of FastAPI servers

launch via 'python cli.py {config_prefix}'

TODO: refactor parse_input, load_config, and hotkey_control into Class
"""

import os
import sys
import requests
import json
from copy import copy
from pprint import pprint
from importlib import import_module

from colorama import init, Fore, Back, Style
from munch import munchify

helao_root = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(helao_root)
from helao import wait_key, validateConfig, Pidd

init()

confPrefix = sys.argv[1]

LAUNCH_ORDER = ["server", "action", "orchestrators", "visualizer"]
# API end points to ignore
IGNORE_ENDS = ['openapi', 'swagger_ui_html', 'swagger_ui_redirect',
               'redoc_html', 'websocket_messages', 'get_all_urls']


def load_config(confPrefix):
    pidd = Pidd(f"pids_{confPrefix}.pck")
    confDict = import_module(f"{confPrefix}").config
    if not validateConfig(pidd, confDict):
        raise Exception(
            Fore.RED + f"Configuration for '{confPrefix}' is invalid.")
    else:
        print(Fore.BLUE + f"Configuration for '{confPrefix}' is valid.")
    active = [k for k,_,_,_ in pidd.list_active()]
    allGroup = {k: {sk: sv for sk, sv in confDict['servers'].items(
    ) if sv['group'] == k and sk in active} for k in LAUNCH_ORDER}
    A = munchify(allGroup)
    cmdDict = {}
    for group in A:
        G = A[group]
        for server in G:
            cmdDict[server] = {}
            S = G[server]
            codeKey = [k for k in S.keys() if k == "fast"]
            if codeKey:
                codeKey = codeKey[0]
                endpoints = requests.get(
                    f"http://{S.host}:{S.port}/endpoints").json()
                filterends = [
                    x for x in endpoints if x['name'] not in IGNORE_ENDS]
                if filterends:
                    print(f"Found {len(filterends)} actions for '{server}'.")
                for x in filterends:
                    y = copy(x)
                    del y['name']
                    y['path'] = f"http://{S.host}:{S.port}{y['path']}"
                    cmdDict[server][x['name']] = y
    return pidd, confDict, cmdDict

def parse_input(string, cmdDict, confDict, pidd):
    baseCommands = ['help', 'list', 'quit', 'shutdown', 'reload']
    head = string.partition(" ")[0]
    body = string.partition(" ")[-1]
    if head == 'help':
        server = body.partition(" ")[0]
        command = body.partition(" ")[-1]
        if server in cmdDict.keys():
            if command in cmdDict[server].keys():
                print(Fore.YELLOW + f"'{command}' calls {cmdDict[server][command]['path']}")
                if 'params' in cmdDict[server][command].keys():
                    print(Fore.YELLOW + f" with 'params' json dict: ")
                    print(Style.RESET_ALL)
                    pprint(cmdDict[server][command]['params'])
            elif command == '':
                S = munchify(confDict['servers'][server])
                print(Fore.YELLOW + f"{server} running at http://{S.host}:{S.port}")
                print(Fore.YELLOW +
                      f"use 'list {server}' to see server actions")
            else:
                print(Fore.YELLOW +
                      f"'{command}' not available for '{server}'")
        elif server == '':
            print(Fore.YELLOW + f"valid commands are:")
            print(Fore.RESET +
                  '\n'.join(baseCommands))
        else:
            print(Fore.YELLOW +
                  f"'{server}' not listed in configuration '{confPrefix}'")
    elif head == 'list':
        server = body.partition(" ")[0]
        command = body.partition(" ")[-1]
        if server == '':
            print(Fore.YELLOW + f"valid server commands for '{confPrefix}':")
            print(Fore.RESET + "\n".join(sorted(
                [f"{srv} {cmd}" for srv in cmdDict.keys() for cmd in cmdDict[srv].keys()])))
        elif server in cmdDict.keys():
            print(Fore.YELLOW + f"valid '{server}' actions:")
            print(Fore.RESET + "\n".join(sorted(
                [f"{server} {cmd}" for cmd in cmdDict[server].keys()])))
        else:
            print(Fore.YELLOW +
                  f"'{server}' not listed in configuration '{confPrefix}'")
    elif head == 'quit':
        return False
    elif head == 'shutdown':
        print(Fore.YELLOW + f"shutting down server group for {confPrefix}")
        pidd.close()
        return False
    elif head == 'reload':
        global pidd_, confDict_, cmdDict_
        pidd_, confDict_, cmdDict_ = load_config(confPrefix)
        print(Fore.BLUE + f"Reloaded {confPrefix}")
    elif head == 'hotkey':
        server1 = body.partition(" ")[0]
        server2 = body.partition(" ")[-1].partition(" ")[0]
        if server1 == '':
            print(Fore.YELLOW + f"'hotkey requires 1 or 2 motor|I/O servers to control'")
        else:
            ioServ = [k for k in cmdDict.keys(
            ) if 'set_digital_out_on' in cmdDict[k].keys() and k in [server1, server2]]
            motorServ = [k for k in cmdDict.keys(
            ) if 'move_live' in cmdDict[k].keys() and k in [server1, server2]]
            if ioServ:
                ioServ = ioServ[0]
                print(Fore.YELLOW +
                      f"using '{ioServ}' for digital I/O control")
            else:
                ioServ = None
            if motorServ:
                motorServ = motorServ[0]
                print(Fore.YELLOW +
                      f"using '{ioServ}' for axis control")
            else:
                motorServ = None
            hotkey_control(motorServ, ioServ)
    else:
        server = head
        if server in cmdDict.keys():
            command = body.partition(" ")[0]
            pars = body.partition(" ")[-1]
            paramDict = json.loads(pars)
            if command in cmdDict[server].keys():
                S = munchify(confDict["servers"][server])
                resp = requests.get(
                    cmdDict[server][command]['path'], params=paramDict).json()
                print(Style.RESET_ALL)
                pprint(resp)
            else:
                print(Fore.YELLOW +
                      f"'{command}' not available for '{server}'")
        else:
            print(Fore.YELLOW +
                  f"'{server}' not listed in configuration '{confPrefix}'")
    return True


def hotkey_control(motorKey, ioKey):
    # provide hotkey interface to I/O and motion
    pass

if __name__ == "__main__":
    pidd_, confDict_, cmdDict_ = load_config(confPrefix)
    print(Fore.BLUE + f"Using configuration {confPrefix}.")
    parse_input('help', cmdDict_, confDict_, pidd_)
    resume = True
    while resume:
        cmdString = input(Fore.GREEN + Style.BRIGHT + f"{confPrefix}>" + Fore.RESET + Back.RESET + Style.NORMAL)
        resume = parse_input(cmdString, cmdDict_, confDict_, pidd_)
    print(Fore.BLUE + "Exiting CLI.")
