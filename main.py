"""
The main entry point for the application
"""
import os
import server as srv
import action as act
import orchestrators as orc
import visualizer as viz
import subprocess

helao_root = os.path.dirname(os.path.realpath(__file__))


def launcher(apis, server, action, orchestrator, visualizer, process):
    for api in apis:
        if api == "server":
            for s in server:
                cmd = [
                    "python", f"{api}/{s}.py"]
                print(f"Starting {api}/{s}")
                subprocess.Popen(cmd, cwd=helao_root, shell=True)
            #ppid = p.pid
        elif api == "action":
            for a in action:
                cmd = [
                "python", f"{api}/{a}.py"]
                print(f"Starting {api}/{a}")
                subprocess.Popen(cmd, cwd=helao_root)
        elif api == "orchestrator":
            for o in orchestrator:
                cmd = [
                "python", f"{api}/{o}.py"]
                print(f"Starting {api}/{o}.py")
                subprocess.Popen(cmd, cwd=helao_root)
        elif api == "visualizer":
            for v in visualizer:
                cmd = ["bokeh", "serve", "--show", f"{api}/{v}.py",
                    "--args", confPrefix, server]
                subprocess.Popen(cmd, cwd=helao_root)
        elif api == "process":
            for p in process:
                cmd = [
                    "python", f"{p}.py"]
                subprocess.Popen(cmd, cwd=helao_root)
                print(f"Starting {o}.py")           
                
    #return ppid




if __name__ == '__main__':
    
    LAUNCH_ORDER = ["server", "action", "orchestrators", "visualizer", "process"]
    server = ["autolab_server", "megsv_server", "minipump_server", "pump_server", "lang_server"]
    action = ["echem", "lang_action", "minipumping", "pump_server", "pumping", "sensing_megsv"]
    orchestrator = ["mischbares"]
    visualizer = ["autolab_visualizer"]
    process = ["process"]
    launcher(LAUNCH_ORDER, server, action, orchestrator, visualizer, process)
    
    
