config = dict()

# action library provides generator functions which produce action
# lists from input decision_id grouping
config["action_libraries"] = ["lisa_ANEC2"]

# we define all the servers here so that the overview is a bit better
config["servers"] = dict(
    nimax=dict(
        host="127.0.0.1",
        port=8006,
        group="server",
        fast="nidaqmx_server",
        params = dict(
            local_data_dump="C:\\temp", # dont foeget to use \\ instead of \
            dev_CellCurrent_trigger = 'PFI1', #P1.1
            dev_CellVoltage_trigger = 'PFI1', #P1.1
            dev_CellCurrent = {
                        '1':'PXI-6289/ai16',
                        '2':'PXI-6289/ai17',
                        '3':'PXI-6289/ai18',
                        '4':'PXI-6289/ai19',
                        '5':'PXI-6289/ai20',
                        '6':'PXI-6289/ai21',
                        '7':'PXI-6289/ai22',
                        '8':'PXI-6289/ai23',
                        '9':'PXI-6289/ai0'
                        },
            dev_CellVoltage = {
                '1':'PXI-6284/ai16',
                '2':'PXI-6284/ai17',
                '3':'PXI-6284/ai18',
                '4':'PXI-6284/ai19',
                '5':'PXI-6284/ai20',
                '6':'PXI-6284/ai21',
                '7':'PXI-6284/ai22',
                '8':'PXI-6284/ai23',
                '9':'PXI-6284/ai0'
                },
            dev_ActiveCellsSelection = {
                '1':'PXI-6289/port0/line23', #P0.23
                '2':'PXI-6289/port0/line24', #P0.24
                '3':'PXI-6289/port0/line25', #P0.25
                '4':'PXI-6289/port0/line26', #P0.26
                '5':'PXI-6289/port0/line27', #P0.27
                '6':'PXI-6289/port0/line28', #P0.28
                '7':'PXI-6289/port0/line29', #P0.29
                '8':'PXI-6289/port0/line30', #P0.30
                '9':'PXI-6289/port0/line31'  #P0.31
                },
            dev_FSWBCDCmd = {
                '1':'PXI-6284/port0/line5', #P0.5
                '2':'PXI-6284/port0/line1', #P0.1
                '3':'PXI-6284/port0/line2', #P0.2
                '4':'PXI-6284/port0/line3'  #P0.3
                },
            dev_GasFlowValves = {
                '1':'PXI-6284/port1/line2', #P1.2
                '2':'PXI-6284/port1/line3', #P1.3
                '3':'PXI-6284/port1/line4', #P1.4
                '4':'PXI-6284/port1/line5', #P1.5
                '5':'PXI-6284/port1/line6', #P1.6
                '6':'PXI-6284/port1/line7', #P1.7
                '7':'PXI-6284/port2/line0', #P2.0
                '8':'PXI-6284/port2/line1', #P2.1
                '9':'PXI-6284/port2/line2'  #P2.2
                },
            dev_MasterCellSelect = {
                '1':'PXI-6284/port0/line23', #P0.23
                '2':'PXI-6284/port0/line24', #P0.24
                '3':'PXI-6284/port0/line25', #P0.25
                '4':'PXI-6284/port0/line26', #P0.26
                '5':'PXI-6284/port0/line27', #P0.27
                '6':'PXI-6284/port0/line28', #P0.28
                '7':'PXI-6284/port0/line29', #P0.29
                '8':'PXI-6284/port0/line30', #P0.30
                '9':'PXI-6284/port0/line31', #P0.31
                'X':'PXI-6284/port0/line22'  #P0.22, two electrode
                },
            dev_Pumps = {
                'PeriPump':'PXI-6284/port0/line4	', #P0.4
                'MultiPeriPump':'PXI-6284/port0/line0' #P0.0
                },
            dev_FSW = {
                'Done':'PXI-6284/port2/line4',  #P2.4
                'Error':'PXI-6284/port2/line6'  #P2.6
                },
            dev_RSHTTLhandshake = {
                'RSH1':'PXI-6284/port2/line5',  #P2.5
                'RSH2':'PXI-6284/port2/line7',  #P2.7
                'RSH3':'PXI-6284/port2/line3',  #P2.3
#                'port':'PXI-6284/ctr0',
#                'term':'/PXI-6284/PFI8' #P2.0
                }
        )
    ),
    potentiostat=dict(
        host="127.0.0.1",
        port=8003,
        group="server",
        fast="gamry_server",
        simulate=False, # choose between simulator(default) or real device
        params=dict(
            #dev_family = 'Interface', # 'Interface' or 'Reference', not need anymore, we can autodetect this
            dev_id = 0, # (default 0) Gamry device number in Gamry Instrument Manager (i-1)
            local_data_dump="C:\\temp", # dont foeget to use \\ instead of \
            #path_to_gamrycom=r"C:\Program Files (x86)\Gamry Instruments\Framework\GamryCOM.exe"
            #path_to_gamrycom=r"C:\Program Files (x86)\Gamry Instruments\Framework 6\GamryCOM.exe"
        )
    ),
    exp_vis=dict(#simple dumb modular visualizer
        host="127.0.0.1",
        port=5008,
        group="visualizer",
        bokeh="bokeh_modular_visualizer",
        params = dict(
            doc_name = "ANEC2 visualizer",
            ws_nidaqmx="nimax",
            ws_potentiostat = 'potentiostat',
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
