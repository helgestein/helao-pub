config = dict()

# we define all the servers here so that the overview is a bit better
config["servers"] = dict(
    potentiostat_vis2=dict(
        host="127.0.0.1",
        port=5007,
        group="visualizer",
        bokeh="bokeh_test",
        params = dict(
            ws_host="potentiostat"
        )
    )
)
