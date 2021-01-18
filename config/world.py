config = dict()

# action library provides generator functions which produce action
# lists from input decision_id grouping
config["action_libraries"] = ["lisa_sdc_demo"]

# we define all the servers here so that the overview is a bit better
config["servers"] = dict(
    motor=dict(
        host="127.0.0.1",
        port=8001,
        group="server",
        fast="galil_motion",
        simulate=True, # choose between simulator(default) or real device
        params=dict(
            count_to_mm=dict(
                A=1.0/3154.787,
                B=1.0/6395.45,
                C=1.0/6395.45,
                D=1.0/6397.95,
                u=154.1133/985482.0
            ),
            galil_ip_str="192.168.200.23",
            def_speed_count_sec=10000,
            max_speed_count_sec=25000,
            ipstr="192.168.200.23",
            axis_id=dict(
                x="D",
                y="B",
                z="C",
                s="A",
                #t="E",
                #u="F"
                ),
            axlett="ABCD",
            timeout = 60 # timeout for axis stop in sec
        )
    ),
    io=dict(
        host="127.0.0.1",
        port=8002,
        group="server",
        fast="galil_io",
        simulate=True, # choose between simulator(default) or real device
        params=dict(
            count_to_mm=dict(
                A=1.0/3154.787,
                B=1.0/6395.45,
                C=1.0/6395.45,
                D=1.0/6397.95,
                u=154.1133/985482.0
            ),
            galil_ip_str="192.168.200.23",
            def_speed_count_sec=10000,
            max_speed_count_sec=25000,
            ipstr="192.168.200.23",
            axis_id=dict(
                x="D",
                y="B",
                z="C",
                s="A",
                #t="E",
                #u="F"
            ),
            axlett="ABCD"
        )
    ),
    potentiostat=dict(
        host="127.0.0.1",
        port=8003,
        group="server",
        fast="gamry_server",
        simulate=True, # choose between simulator(default) or real device
        params=dict(
            temp_dump=".\temp",
            path_to_gamrycom=r"C:\Program Files (x86)\Gamry Instruments\Framework\GamryCOM.exe"
        )
    ),
    orchestrator=dict(
        host="127.0.0.1",
        port=8010,
        group="orchestrators",
        fast="async_orch",
        path="."
    ),
    potentiostat_vis=dict(
        host="127.0.0.1",
        port=5006,
        group="visualizer",
        bokeh="bokeh_test",
        params = dict(
            ws_host="potentiostat"
        )
    )
)
