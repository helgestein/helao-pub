import os
import sys
import websockets
import json
import collections
from functools import partial
from importlib import import_module
import sys
sys.path.append("../config")
sys.path.append("../driver")

from bokeh.models import ColumnDataSource, CheckboxButtonGroup, RadioButtonGroup
from bokeh.models import Title, DataTable, TableColumn
from bokeh.models.widgets import Paragraph
from bokeh.plotting import figure, curdoc
from tornado.ioloop import IOLoop
#from mischbares_small import config
import os
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
config = import_module(sys.argv[1]).config


S = config['servers']['autolabDriver']
uri = f"ws://{S['host']}:{S['port']}/ws"

doc = curdoc()
time_stamp = 0
pids = collections.deque(10*[0], 10)

def update(new_data):
    global source
    print(new_data)
    source.stream(new_data)
    print(source.to_json(False))

def remove_line(new_time_stamp):
    global time_stamp
    global source
    global plot
    global data_table

    doc.remove_root(plot)
    doc.remove_root(data_table)

    time_stamp = new_time_stamp

    plot = figure(title=str(new_time_stamp), height=300)
    plot.title.align = "center"
    plot.title.text_font_size = "24px"
    xstr = ''
    if(radio_button_group.active == 0):
        xstr = 't_s'
        plot.add_layout(Title(text="t_s", align="center"), "below")
    elif(radio_button_group.active == 1):
        xstr = 'freq'
        plot.add_layout(Title(text="freq", align="center"), "below")
    elif(radio_button_group.active == 2):
        plot.add_layout(Title(text="Ewe_V", align="center"), "below")
        xstr = 'Ewe_V'
    elif(radio_button_group.active == 3):
        plot.add_layout(Title(text="Ach_V", align="center"), "below")
        xstr = 'Ach_V'
    elif(radio_button_group.active == 4):
        plot.add_layout(Title(text="Z_real", align="center"), "below")
        xstr = 'Z_real'
    elif(radio_button_group.active == 5):
        plot.add_layout(Title(text="Z_imag", align="center"), "below")
        xstr = 'Z_imag'
    elif(radio_button_group.active == 6):
        plot.add_layout(Title(text="phase", align="center"), "below")
        xstr = 'phase'
    elif(radio_button_group.active == 7):
        plot.add_layout(Title(text="modulus", align="center"), "below")
        xstr = 'modulus'
    else:
        plot.add_layout(Title(text="I_A", align="center"), "below")
        xstr = 'I_A'

    colors = ['red', 'blue', 'yellow', 'green', 'pink', 'brown', 'olive', 'cyan', 'grey']
    color_count = 0
    for i in checkbox_button_group.active:
        if i == 0:
            plot.add_layout(Title(text="t_s", align="center"), "left")
            print(source.to_json(True))
            plot.line(x=xstr, y='t_s', line_color=colors[color_count], source=source, name=str(time_stamp))
        elif i == 1:
            plot.add_layout(Title(text="freq", align="center"), "left")
            plot.line(x=xstr, y='freq', line_color=colors[color_count], source=source, name=str(time_stamp))
        elif i == 2:
            plot.add_layout(Title(text="Ewe_V", align="center"), "left")
            print(source.to_json(True))
            plot.line(x=xstr, y='Ewe_V', line_color=colors[color_count], source=source, name=str(time_stamp))
        elif i == 3:
            plot.add_layout(Title(text="Ach_V", align="center"), "left")
            plot.line(x=xstr, y='Ach_V', line_color=colors[color_count], source=source, name=str(time_stamp))
        elif i == 4:
            plot.add_layout(Title(text="Z_real", align="center"), "left")
            plot.line(x=xstr, y='Z_real', line_color=colors[color_count], source=source, name=str(time_stamp))
        elif i == 5:
            plot.add_layout(Title(text="Z_imag", align="center"), "left")
            plot.line(x=xstr, y='Z_imag', line_color=colors[color_count], source=source, name=str(time_stamp))
        elif i == 6:
            plot.add_layout(Title(text="phase", align="center"), "left")
            plot.line(x=xstr, y='phase', line_color=colors[color_count], source=source, name=str(time_stamp))
        elif i == 7:
            plot.add_layout(Title(text="modulus", align="center"), "left")
            plot.line(x=xstr, y='modulus', line_color=colors[color_count], source=source, name=str(time_stamp))   
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

source = ColumnDataSource(data=dict(t_s=[], freq= [], Ewe_V=[], Ach_V=[], Z_real=[], Z_imag=[], phase=[], modulus=[], I_A=[]))

paragraph1 = Paragraph(text="""x-axis:""", width=50, height=15)
radio_button_group = RadioButtonGroup(labels=["t_s", "freq", "Ewe_V", "Ach_V", "Z_real", "Z_imag", "phase", "modulus","I_A"], active=0)
paragraph2 = Paragraph(text="""y-axis:""", width=50, height=15)
checkbox_button_group = CheckboxButtonGroup(labels=["t_s", "freq", "Ewe_V", "Ach_V", "Z_real", "Z_imag", "phase", "modulus", "I_A"], active=[1])

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





