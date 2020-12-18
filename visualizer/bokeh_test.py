
import os
import sys
import websockets
import json
import collections
from functools import partial
from importlib import import_module

from bokeh.models import ColumnDataSource, CheckboxButtonGroup, RadioButtonGroup
from bokeh.models import Title, DataTable, TableColumn
from bokeh.models.widgets import Paragraph
from bokeh.plotting import figure, curdoc
from tornado.ioloop import IOLoop
from munch import munchify

# not packaging as module for now, so detect source code's root directory from CLI execution
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
# append config folder to path to allow dynamic config imports
sys.path.append(os.path.join(helao_root, 'config'))
# grab config file prefix (e.g. "world" for world.py) from CLI argument
confPrefix = sys.argv[1]
# grab server key from CLI argument, this is a unique name for the server instance
servKey = sys.argv[2]
# import config dictionary
config = import_module(f"{confPrefix}").config
# shorthand object-style access to config dictionary
C = munchify(config)["servers"]
# config dict for visualization server
O = C[servKey]
# config dict for websocket host
S = C[O.params.ws_host]

doc = curdoc()
uri = f"ws://{S.host}:{S.port}/{O.params.ws_host}/ws_data"
time_stamp = 0
pids = collections.deque(10*[0], 10)

def update(new_data):
    print(new_data)
    source.stream(new_data)

def remove_line(new_time_stamp):
    global time_stamp
    global source
    global plot
    global data_table

    doc.remove_root(plot)
    doc.remove_root(data_table)
    source.data = {k: [] for k in source.data}

    time_stamp = new_time_stamp

    plot = figure(title=str(new_time_stamp), height=300)
    plot.title.align = "center"
    plot.title.text_font_size = "24px"
    xstr = ''
    if(radio_button_group.active == 0):
        xstr = 't_s'
        plot.add_layout(Title(text="t_s", align="center"), "below")
    elif(radio_button_group.active == 1):
        plot.add_layout(Title(text="Ewe_V", align="center"), "below")
        xstr = 'Ewe_V'
    elif(radio_button_group.active == 2):
        plot.add_layout(Title(text="Ach_V", align="center"), "below")
        xstr = 'Ach_V'
    else:
        plot.add_layout(Title(text="I_A", align="center"), "below")
        xstr = 'I_A'
    colors = ['red', 'blue', 'yellow', 'green']
    color_count = 0
    for i in checkbox_button_group.active:
        if i == 0:
            plot.add_layout(Title(text="t_s", align="center"), "left")
            plot.line(x=xstr, y='t_s', line_color=colors[color_count], source=source, name=str(time_stamp))
        elif i == 1:
            plot.add_layout(Title(text="Ewe_V", align="center"), "left")
            plot.line(x=xstr, y='Ewe_V', line_color=colors[color_count], source=source, name=str(time_stamp))
        elif i == 2:
            plot.add_layout(Title(text="Ach_V", align="center"), "left")
            plot.line(x=xstr, y='Ach_V', line_color=colors[color_count], source=source, name=str(time_stamp))
        else:
            plot.add_layout(Title(text="I_A", align="center"), "left")
            plot.line(x=xstr, y='I_A', line_color=colors[color_count], source=source, name=str(time_stamp))
        color_count += 1

    pids.appendleft(new_time_stamp)
    pid_list = dict(
        pids=[pids[i] for i in range(10)],
    )
    pid_source = ColumnDataSource(pid_list)
    columns = [
        TableColumn(field="pids", title="PIDs"),
    ]
    data_table = DataTable(source=pid_source, columns=columns, width=400, height=280)

    doc.add_root(plot) # add plot to document
    doc.add_root(data_table)


async def loop(): # non-blocking coroutine, updates data source
    async with websockets.connect(uri) as ws:
        while True:
            new_data = await ws.recv()
            new_data=json.loads(new_data)
            if(type(new_data) == float):
                if(new_data != time_stamp): 
                    doc.add_next_tick_callback(partial(remove_line, new_data))
            else:
                doc.add_next_tick_callback(partial(update, new_data))

source = ColumnDataSource(data=dict(t_s=[], Ewe_V=[], Ach_V=[], I_A=[]))

paragraph1 = Paragraph(text="""x-axis:""", width=50, height=15)
radio_button_group = RadioButtonGroup(labels=["t_s", "Ewe_V", "Ach_V", "I_A"], active=0)
paragraph2 = Paragraph(text="""y-axis:""", width=50, height=15)
checkbox_button_group = CheckboxButtonGroup(labels=["t_s", "Ewe_V", "Ach_V", "I_A"], active=[1])

plot = figure(title="Title", height=300)
line1 = plot.line(x='t_s', y='Ewe_V', source=source, name=str(time_stamp))

pid_list = dict(
    pids=[pids[i] for i in range(10)],
)
pid_source = ColumnDataSource(pid_list)
columns = [
    TableColumn(field="pids", title="PIDs"),
]
data_table = DataTable(source=pid_source, columns=columns, width=400, height=280)

doc.add_root(paragraph1)
doc.add_root(radio_button_group)
doc.add_root(paragraph2)
doc.add_root(checkbox_button_group)
doc.add_root(plot) # add plot to document
doc.add_root(data_table)

IOLoop.current().spawn_callback(loop) # add coro to IOLoop





