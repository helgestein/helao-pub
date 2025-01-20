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
                cmd = ["python", f"{api}/{s}.py", sys.argv[1]]
                print(f"Starting {api}/{s}")
                subprocess.Popen(cmd, cwd=helao_root, shell=True)
        elif api == "action":
            for a in action:
                cmd = ["python", f"{api}/{a}.py", sys.argv[1]]
                print(f"Starting {api}/{a}")
                subprocess.Popen(cmd, cwd=helao_root)
        elif api == "orchestrators":
            for o in orchestrator:
                cmd = ["python", f"{api}/{o}.py", sys.argv[1]]
                print(f"Starting {api}/{o}.py")
                subprocess.Popen(cmd, cwd=helao_root)
        elif api == "visualizer":
            for v in visualizer:
                print(f"Starting {api}/{v}.py")
                if "autolab" in v or "hits" in v:
                    print("Bokeh server is starting")
                    cmd = ["bokeh", "serve", "--show", f"{api}/{v}.py", "--args", sys.argv[1]]
                else:
                    print("Python server is starting")
                    cmd = ["python", f"{v}.py"]    
                print(f"Starting {api}/{v}.py")
                subprocess.Popen(cmd, cwd=helao_root)
        elif api == "process":
            for p in process:
                cmd = ["python", f"{p}.py", sys.argv[1]]
                print(f"Starting process {p}.py")
                subprocess.Popen(cmd, cwd=helao_root)
                           
                




if __name__ == '__main__':
    
    LAUNCH_ORDER = ["server", "action", "orchestrators", "visualizer", "process"]
    server = config['launch']['server']
    action = config['launch']['action']
    orchestrator = config['launch']['orchestrator']
    visualizer = config['launch']['visualizer']
    process = config['launch']['process']
    launcher(LAUNCH_ORDER, server, action, orchestrator, visualizer, process)
    
    
