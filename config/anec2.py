config = dict()

# action library provides generator functions which produce action
# lists from input decision_id grouping
#config["action_libraries"] = ["lisa_sdc_demo"]
config["action_libraries"] = ["lisa_ANEC2"]

# we define all the servers here so that the overview is a bit better
config["servers"] = dict(
    motor=dict(
        host="127.0.0.1",
        port=8001,
        group="server",
        fast="galil_motion",
        simulate=False, # choose between simulator(default) or real device
        params=dict(
            Transfermatrix = [[1,0,0],[0,1,0],[0,0,1]], # default Transfermatrix for plate calibration
            M_instr = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]], # instrument specific calibration
            count_to_mm=dict(
                A=1.0/15835.31275,#1.0/15690.3,
                B=1.0/6398.771436,#1.0/6395.45,
                C=1.0/6396.315722,#1.0/6395.45,
                D=1.0/3154.787,#1.0/3154.787,
            ),
            galil_ip_str="192.168.200.23",
            def_speed_count_sec=10000,
            max_speed_count_sec=25000,
            ipstr="192.168.200.23",
            axis_id=dict(
                x="C",
                y="B",
                z="A",
                Rz="D",
                #t="E",
                #u="F"
                ),
            axis_zero=dict(
                A=0.0, #z
                B=52.0, #y
                C=77.0, #x
                D=0.0, #Rz
                #t="E",
                #u="F"
                ),
            #axlett="ABCD", # not needed anymore
            timeout = 10*60, # timeout for axis stop in sec
            tbroadcast = 2, # frequency of websocket broadcast (only broadcasts if something changes but need to reduce the frequeny of that if necessary)
        )
    ),
    data=dict(
        host="127.0.0.1",
        port=8004,
        group="server",
        fast="HTEdata_server",
        mode = "legacy", # lagcy; modelyst
        params = dict(
        )
    ),
    aligner=dict(
        host="127.0.0.1",
        port=8005,
        group="server",
        fast="alignment_server",
        params = dict(
            data_server = "data", # will use this to get PM_map temporaily, else need to parse it as JSON later
            motor_server = "motor", # will use this to get PM_map temporaily, else need to parse it as JSON later
            vis_server = "aligner_vis", # will use this to get PM_map temporaily, else need to parse it as JSON later
            cutoff = 6, # cutoff of digits for TransferMatrix calculation
        )
    ),
    aligner_vis=dict(
        host="127.0.0.1",
        port=5007,
        group="action",
        bokeh="bokeh_platealigner",
        params = dict(
            aligner_server="aligner", # aligner and aligner_vis should be in tandem
        )
    ),
    orchestrator=dict(
        host="127.0.0.1",
        port=8010,
        group="orchestrators",
        fast="async_orch",
        path="."
    ),

)
