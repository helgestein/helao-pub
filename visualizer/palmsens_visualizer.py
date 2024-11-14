import json
import asyncio
import requests
import websockets
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import queue
import threading
import numpy as np
import sys
import os
from importlib import import_module

sys.path.append('../driver')
sys.path.append('../config')
sys.path.append('../server')

#helao_root = os.path.dirname(os.path.realpath(__file__))
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
config_path = sys.path.append(os.path.join(helao_root, 'config'))
config = import_module(sys.argv[1]).config
serverkey = sys.argv[2]

orchestrator_url = config[serverkey]["orchestrator_url"]
socket_url = config["plot_process"]["socket_url"]

# Style sheet and font properties
plt.style.use('ggplot')
plt.rcParams.update({
    'axes.labelweight': 'bold',
    'axes.labelsize': 'large',
    'axes.titleweight': 'bold',
    'axes.titlesize': 'large'
})

experiment_keys = [
    ("x", "y"),
    ("zre", "zim")
]
# the lower index the mroe important if more than one pair is present
#  in one measurement the lower index one is displayed

# Data queues
data_queue = queue.Queue()
received_data = []
xdata, ydata, timestamps = [], [], []
start_time = -1
index = -1
clear_flag = False
experiment_index = 0
#label_x = "x"
#label_y = "y"
x_label = "x"
y_label = "y"

# Data generator coroutine
async def data_generator(queue):
    global start_time
    global index
    global experiment_index
    global clear_flag
    #global label_x
    #global label_y
    global x_label
    global y_label
    async with websockets.connect(socket_url, ping_interval=None) as ws:
        while True:
            new_data = await ws.recv()
            await asyncio.sleep(0.1)
            new_data = json.loads(new_data)
            if isinstance(new_data, dict):
                received_data.append(new_data)
                if new_data["index"] <= index and index != -1:
                    experiment_index += 1
                    clear_flag = True
                index = new_data["index"]
                for keys_x, keys_y in experiment_keys:
                    if keys_x in new_data and keys_y in new_data:
                        x = new_data[keys_x]
                        y = new_data[keys_y]
                        if keys_x == "x" and keys_y == "y":
                            x_type = new_data["x_type"]
                            x_unit = new_data["x_unit"]
                            x_label = f"{x_type}, {x_unit}"
                            y_type = new_data["y_type"]
                            y_unit = new_data["y_unit"]
                            y_label = f"{y_type}, {y_unit}"
                        else:
                            x_label = keys_x
                            y_label = keys_y
                        if isinstance(x, list):
                            x = x[0]
                        if isinstance(y, list):
                            y = y[0]
                        
                        if start_time == -1:
                            start_time =  new_data["timestamp"] * 1000
                        
                        timestamp = new_data["timestamp"] * 1000 - start_time
                        #label_x = keys_x
                        #label_y = keys_y
                        queue.put_nowait((x, y, timestamp))
                        
                        break
            else:
                print(f"Received data is not a dictionary")

# Function to start the data generator in a separate thread
def start_data_generator():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(data_generator(data_queue))



# Matplotlib plot setup
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), height_ratios=[4, 1])
line = ax1.scatter(xdata, ydata, color='r')
timestamps_line, = ax2.plot(timestamps, 'b-')

ax1.set_xlim(0, 10)
ax1.set_ylim(0, 10)
ax2.set_xlim(0, 10)
ax2.set_ylim(0, 10)

#ax1.set_xlabel(label_x)
#ax1.set_ylabel(label_y)
ax1.set_xlabel(x_label)
ax1.set_ylabel(y_label)
ax1.set_title('Real-time data plot')
ax2.set_xlabel('Index')
ax2.set_ylabel('Timestamp')



# Initialization function for FuncAnimation
def init():
    #line.set_data([], [])
    timestamps_line.set_data([], [])
    return line, timestamps_line

# Update function for FuncAnimation
def update(frame):
    global line  # Declare line as global to update it in this function
    global clear_flag
    global label_x
    global label_y
    while not data_queue.empty():
        x, y, timestamp = data_queue.get_nowait()
        if clear_flag:
            xdata.clear()
            ydata.clear()
            timestamps.clear()
            clear_flag = False
        xdata.append(x)
        ydata.append(y)
        timestamps.append(timestamp)

    ax1.clear()  # Clear previous scatter plot
    #ax1.set_xlabel(label_x)
    #ax1.set_ylabel(label_y)
    ax1.set_xlabel(x_label)
    ax1.set_ylabel(y_label)
    ax1.set_title('Real-time data plot')
    x_min = min(xdata, default=0)
    x_max = max(xdata, default=10)
    y_min = min(ydata, default=0)
    y_max = max(ydata, default=10)
    ax1.set_xlim(x_min - 0.05 * abs(x_min), x_max + 0.05 * abs(x_max))
    ax1.set_ylim(y_min - 0.05 * abs(y_min), y_max + 0.05 * abs(y_max))
    line = ax1.scatter(xdata, ydata, color='r')  # Redraw scatter plot with updated data
    timestamps_line.set_data(range(len(timestamps)), timestamps)
    if len(timestamps) > 1:
        ax2.set_xlim(0, len(timestamps) - 1)
    else:
        ax2.set_xlim(0, 1)
    ax2.set_ylim(min(timestamps, default=0), max(timestamps, default=10))
    return line, timestamps_line

# Start the data generator in a separate thread
thread = threading.Thread(target=start_data_generator)
thread.start()

# Start the animation
ani = animation.FuncAnimation(fig, update, init_func=init, blit=False, interval=10, save_count=10000)
# Show the plot
plt.show()
