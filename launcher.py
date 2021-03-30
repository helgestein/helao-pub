"""
The main entry point for the application
"""
import os
import sys
import subprocess
from importlib import import_module

helao_root = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(helao_root, 'config'))
config = import_module(sys.argv[1]).config


def launcher(apis, server, action, orchestrator, visualizer, process):
    for api in apis:
        if api == "server":
            for s in server:
                cmd = ["python", f"{api}/{s}.py"]
                print(f"Starting {api}/{s}")
                subprocess.Popen(cmd, cwd=helao_root, shell=True)
            #ppid = p.pid
        elif api == "action":
            for a in action:
                cmd = ["python", f"{api}/{a}.py"]
                print(f"Starting {api}/{a}")
                subprocess.Popen(cmd, cwd=helao_root)
        elif api == "orchestrators":
            for o in orchestrator:
                cmd = ["python", f"{api}/{o}.py"]
                print(f"Starting {api}/{o}.py")
                subprocess.Popen(cmd, cwd=helao_root)
        elif api == "visualizer":
            for v in visualizer:
                cmd = ["bokeh", "serve", "--show", f"{api}/{v}.py"]
                subprocess.Popen(cmd, cwd=helao_root)
        elif api == "process":
            for p in process:
                cmd = ["python", f"{p}.py"]
                subprocess.Popen(cmd, cwd=helao_root)
                print(f"Starting {o}.py")           
                
    #return ppid




if __name__ == '__main__':
    
    LAUNCH_ORDER = ["server", "action", "orchestrators", "visualizer", "process"]
    server = config['launcher']['server']
    action = config['launcher']['action']
    orchestrator = config['launcher']['mischbares']
    visualizer = config['launcher']['visualizer']
    process = config['launcher']['process']

    config
    launcher(LAUNCH_ORDER, server, action, orchestrator, visualizer, process)
    
    
