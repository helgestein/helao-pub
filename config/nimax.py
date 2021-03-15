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
            Ain_id={'PXI-6289': dict(
                    AI16 = 'CellCurrent_ICell1',
                    AI17 = 'CellCurrent_ICell2',
                    AI18 = 'CellCurrent_ICell3',
                    AI19 = 'CellCurrent_ICell4',
                    AI20 = 'CellCurrent_ICell5',
                    AI21 = 'CellCurrent_ICell6',
                    AI22 = 'CellCurrent_ICell7',
                    AI23 = 'CellCurrent_ICell8',
                    AI0 = 'CellCurrent_ICell9',
                    ),
                'PXI-6284': dict(
                    AI16 = 'CellDiffV_DVCell1',
                    AI17 = 'CellDiffV_DVCell2',
                    AI18 = 'CellDiffV_DVCell3',
                    AI19 = 'CellDiffV_DVCell4',
                    AI20 = 'CellDiffV_DVCell5',
                    AI21 = 'CellDiffV_DVCell6',
                    AI22 = 'CellDiffV_DVCell7',
                    AI23 = 'CellDiffV_DVCell8',
                    AI0 = 'CellDiffV_DVCell9',                
                    ),
                },
            Dout_id={
                'PXI-6289': dict(
                    port1_DO23 = 'cell1_active',
                    port1_DO24 = 'cell2_active',
                    port1_DO25 = 'cell3_active',
                    port1_DO26 = 'cell4_active',
                    port1_DO27 = 'cell5_active',
                    port1_DO28 = 'cell6_active',
                    port1_DO29 = 'cell7_active',
                    port1_DO30 = 'cell8_active',
                    port1_DO31 = 'cell9_active',
                    ),
                'PXI-6284': dict(
                    port0_DO0 = 'FSWBCDCmd_DO0',
                    port0_DO1 = 'FSWBCDCmd_DO1',
                    port0_DO2 = 'FSWBCDCmd_DO2',
                    port0_DO3 = 'FSWBCDCmd_DO3',
                    port1_DO2 = 'GasFlowValve_Cell1',
                    port1_DO3 = 'GasFlowValve_Cell2',
                    port1_DO4 = 'GasFlowValve_Cell3',
                    port1_DO5 = 'GasFlowValve_Cell4',
                    port1_DO6 = 'GasFlowValve_Cell5',
                    port1_DO7 = 'GasFlowValve_Cell6',
                    port2_DO7 = 'GasFlowValve_Cell7',
                    port2_DO1 = 'GasFlowValve_Cell8',
                    port2_DO2 = 'GasFlowValve_Cell9',
                    port0_DO23 = 'MasterCellSelect_RYCell1',
                    port0_DO24 = 'MasterCellSelect_RYCell2',
                    port0_DO25 = 'MasterCellSelect_RYCell3',
                    port0_DO26 = 'MasterCellSelect_RYCell4',
                    port0_DO27 = 'MasterCellSelect_RYCell5',
                    port0_DO28 = 'MasterCellSelect_RYCell6',
                    port0_DO29 = 'MasterCellSelect_RYCell7',
                    port0_DO30 = 'MasterCellSelect_RYCell8',
                    port0_DO31 = 'MasterCellSelect_RYCell9',
                    port0_DO22 = 'MasterCellSelect_RYCellX',
                    port1_DO0 = 'PumpsCmd_PeriPumpCntl',
                    port1_DO1 = 'PumpsCmd_MultiChPeriPumpCntl',
                    ),
                }
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
