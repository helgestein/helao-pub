from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, curdoc
from functools import partial
from tornado.ioloop import IOLoop
from bokeh.models import CheckboxButtonGroup
from bokeh.models import RadioButtonGroup
from bokeh.models.widgets import Paragraph
import asyncio
import websockets
import json

from bokeh.plotting import show
from bokeh.io import output_notebook
from bokeh.models import Range1d, ColumnDataSource
from bokeh.models.renderers import GlyphRenderer

import numpy as np


doc = curdoc()

uri = "ws://localhost:8003/ws"
# ws = websockets()
# ws.connect(uri)

time_stamp = 0

def update(new_data):
    print(new_data)
    source.stream(new_data)

# def remove_glyphs(figure, glyph_name_list):
#     renderers = figure.select(dict(type=GlyphRenderer))
#     for r in renderers:
#         if r.name in glyph_name_list:
#             col = r.glyph.y
#             r.data_source.data[col] = [np.nan] * len(r.data_source.data[col])

def remove_line(new_time_stamp):
    global time_stamp
    global source
    global plot
    # global line1

    doc.remove_root(plot)
    source.data = {k: [] for k in source.data}

    # line = plot.select_one({'name': str(time_stamp)})
    # line.visible = False
    time_stamp = new_time_stamp
    # source = ColumnDataSource(data=dict(t_s=[], Ewe_V=[], Ach_V=[], I_A=[]))

    plot = figure(height=300)
    if(radio_button_group.active == 0):
        plot.line(x='t_s', y='Ewe_V', source=source, name=str(time_stamp))
    elif(radio_button_group.active == 1):
        plot.line(x='Ewe_V', y='Ewe_V', source=source, name=str(time_stamp))
    elif(radio_button_group.active == 2):
        plot.line(x='Ach_V', y='Ewe_V', source=source, name=str(time_stamp))
    else:
        plot.line(x='I_A', y='Ewe_V', source=source, name=str(time_stamp))
    
    doc.add_root(plot) # add plot to document


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

plot = figure(height=300)
line1 = plot.line(x='t_s', y='Ewe_V', source=source, name=str(time_stamp))

doc.add_root(paragraph1)
doc.add_root(radio_button_group)
doc.add_root(paragraph2)
doc.add_root(checkbox_button_group)
doc.add_root(plot) # add plot to document
IOLoop.current().spawn_callback(loop) # add coro to IOLoop





