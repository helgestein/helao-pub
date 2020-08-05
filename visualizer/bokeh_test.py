from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, curdoc
from functools import partial
from tornado.ioloop import IOLoop

import asyncio
import websockets
import json


doc = curdoc()

uri = "ws://localhost:8003/ws"
# ws = websockets()
# ws.connect(uri)

def update(new_data):
    new_data=json.loads(new_data)
    print(new_data)
    source.stream(new_data)

async def loop():
    async with websockets.connect(uri) as ws:
        while True:
            new_data = await ws.recv()
            doc.add_next_tick_callback(partial(update, new_data))

source = ColumnDataSource(data=dict(t_s=[], Ewe_V=[], Ach_V=[], I_A=[]))

plot = figure(height=300)
plot.line(x='t_s', y='Ewe_V', source=source)

doc.add_root(plot)
IOLoop.current().spawn_callback(loop)