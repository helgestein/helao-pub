from enum import Enum
import nidaqmx
from nidaqmx.constants import LineGrouping
from nidaqmx.constants import Edge
from nidaqmx.constants import AcquisitionType
from nidaqmx.constants import TerminalConfiguration
from nidaqmx.constants import VoltageUnits
from nidaqmx.constants import CurrentShuntResistorLocation
from nidaqmx.constants import UnitsPreScaled
from nidaqmx.constants import TriggerType
from nidaqmx.constants import CountDirection
from nidaqmx.constants import TaskMode
from nidaqmx.constants import SyncType


class pumpitems(str, Enum):
    PeriPump = "PeriPump"
    # MultiPeriPump = 'MultiPeriPump'
    Direction = "Direction"


class cNIMAX:
    # in principle we can also just call predefined tasks from NImax app,
    # but I define my own here to be more flexible

    def __init__(self, config_dict, stat):
        self.config_dict = config_dict
        print(" ... init NI-MAX")
        # will get the statushandler from the server to set the idle status after measurment
        self.stat = stat

        if not "local_data_dump" in self.config_dict:
            self.config_dict["local_data_dump"] = "C:\\temp"

        self.local_data_dump = self.config_dict["local_data_dump"]

        # seems to work by just defining the scale and then only using its name
        try:
            self.Iscale = nidaqmx.scale.Scale.create_lin_scale(
                "NEGATE3", -1.0, 0.0, UnitsPreScaled.AMPS, "AMPS"
            )
        except Exception as e:
            print("##########################################################")
            print(" ... NImax error")
            print("##########################################################")
            raise e
        self.time_stamp = time.time()

        self.qIV = asyncio.Queue(maxsize=100)  # ,loop=asyncio.get_event_loop())
        self.qsettings = asyncio.Queue(maxsize=100)  # ,loop=asyncio.get_event_loop())
        # this defines the time axis, need to calculate our own
        self.samplingrate = 10  # samples per second
        # used to keep track of time during data readout
        self.IVtimeoffset = 0.0
        self.buffersize = 1000  # finite samples or size of buffer depending on mode

        self.task_CellCurrent = None
        self.task_CellVoltage = None
        self.task_IV_run = False
        self.IO_estop = False
        self.activeCell = [False for _ in range(9)]

        # for saving data localy
        self.datafile = LocalDataHandler()
        self.FIFO_epoch = None
        # self.FIFO_header = ''
        self.FIFO_NImaxheader = (
            ""  # measuement specific, will be reset each measurement
        )
        self.FIFO_name = ""
        self.FIFO_dir = ""
        self.FIFO_column_headings = [
            "t_s",
            "ICell1_A",
            "ICell2_A",
            "ICell3_A",
            "ICell4_A",
            "ICell5_A",
            "ICell6_A",
            "ICell7_A",
            "ICell8_A",
            "ICell9_A",
            "ECell1_V",
            "ECell2_V",
            "ECell4_V",
            "ECell4_V",
            "ECell5_V",
            "ECell6_V",
            "ECell7_V",
            "ECell8_V",
            "ECell9_V",
        ]

        # holds all sample information
        self.FIFO_sample = sample_class()

    def create_IVtask(self, tstep):
        self.samplingrate = 1.0 / tstep

        # Voltage reading is MASTER
        self.task_CellCurrent = nidaqmx.Task()
        for myname, mydev in self.config_dict.dev_CellCurrent.items():
            self.task_CellCurrent.ai_channels.add_ai_current_chan(
                mydev,
                name_to_assign_to_channel="Cell_" + myname,
                terminal_config=TerminalConfiguration.DIFFERENTIAL,
                min_val=-0.02,
                max_val=+0.02,
                units=VoltageUnits.FROM_CUSTOM_SCALE,
                shunt_resistor_loc=CurrentShuntResistorLocation.EXTERNAL,
                ext_shunt_resistor_val=5.0,
                custom_scale_name="NEGATE3",  # TODO: this can be a per channel calibration
            )
        self.task_CellCurrent.ai_channels.all.ai_lowpass_enable = True
        self.task_CellCurrent.timing.cfg_samp_clk_timing(
            self.samplingrate,
            source="",
            active_edge=Edge.RISING,
            sample_mode=AcquisitionType.CONTINUOUS,
            samps_per_chan=self.buffersize,
        )
        # TODO can increase the callbackbuffersize if needed
        # self.task_CellCurrent.register_every_n_samples_acquired_into_buffer_event(10,self.streamCURRENT_callback)
        self.task_CellCurrent.register_every_n_samples_acquired_into_buffer_event(
            10, self.streamIV_callback
        )

        # Voltage reading is SLAVE
        # we cannot combine both tasks into one as they run on different DAQs
        # define the VOLT and CURRENT task as they need to stay in memory
        self.task_CellVoltage = nidaqmx.Task()
        for myname, mydev in self.config_dict.dev_CellVoltage.items():
            self.task_CellVoltage.ai_channels.add_ai_voltage_chan(
                mydev,
                name_to_assign_to_channel="Cell_" + myname,
                terminal_config=TerminalConfiguration.DIFFERENTIAL,
                min_val=-10.0,
                max_val=+10.0,
                units=VoltageUnits.VOLTS,
            )

        # does this globally enable lowpass or only for channels in task?
        self.task_CellVoltage.ai_channels.all.ai_lowpass_enable = True
        # self.task_CellVoltage.ai_lowpass_enable = True
        self.task_CellVoltage.timing.cfg_samp_clk_timing(
            self.samplingrate,
            source="",
            active_edge=Edge.RISING,
            sample_mode=AcquisitionType.CONTINUOUS,
            samps_per_chan=self.buffersize,
        )
        # each card need its own physical trigger input

        if (
            self.config_dict.dev_CellVoltage_trigger != ""
            and self.config_dict.dev_CellCurrent_trigger != ""
        ):
            self.task_CellVoltage.triggers.start_trigger.trig_type = (
                TriggerType.DIGITAL_EDGE
            )
            self.task_CellVoltage.triggers.start_trigger.cfg_dig_edge_start_trig(
                trigger_source=self.config_dict.dev_CellVoltage_trigger,
                trigger_edge=Edge.RISING,
            )

            self.task_CellCurrent.triggers.start_trigger.trig_type = (
                TriggerType.DIGITAL_EDGE
            )
            self.task_CellCurrent.triggers.start_trigger.cfg_dig_edge_start_trig(
                trigger_source=self.config_dict.dev_CellCurrent_trigger,
                trigger_edge=Edge.RISING,
            )

    def streamIV_callback(
        self, task_handle, every_n_samples_event_type, number_of_samples, callback_data
    ):
        # TODO: how to turn task_handle into the task object?
        if self.task_IV_run and not self.IO_estop:
            try:
                # start seq: V then current, so read current first then Volt
                # put callback only on current (Volt should the always have enough points)
                # readout is requested-1 when callback is on requested
                dataI = self.task_CellCurrent.read(
                    number_of_samples_per_channel=number_of_samples
                )
                dataV = self.task_CellVoltage.read(
                    number_of_samples_per_channel=number_of_samples
                )
                # this is also what NImax seems to do
                time = [
                    self.IVtimeoffset + i / self.samplingrate
                    for i in range(len(dataI[0]))
                ]
                # update timeoffset
                self.IVtimeoffset += number_of_samples / self.samplingrate
                # print(' ... NImax VOLT data: ',data)
                if self.qIV.full():
                    print(" ... NImax qIV is full ...")
                    _ = self.qIV.get_nowait()
                new_data = {"t_s": time, "I_A": dataI, "E_V": dataV}
                self.qIV.put_nowait(new_data)

                for i in range(len(dataI[0])):
                    self.datafile.write_data_sync(
                        str(new_data["t_s"][i])
                        + "\t"
                        + str(new_data["I_A"][0][i])
                        + "\t"
                        + str(new_data["I_A"][1][i])
                        + "\t"
                        + str(new_data["I_A"][2][i])
                        + "\t"
                        + str(new_data["I_A"][3][i])
                        + "\t"
                        + str(new_data["I_A"][4][i])
                        + "\t"
                        + str(new_data["I_A"][5][i])
                        + "\t"
                        + str(new_data["I_A"][6][i])
                        + "\t"
                        + str(new_data["I_A"][7][i])
                        + "\t"
                        + str(new_data["I_A"][8][i])
                        + "\t"
                        + str(new_data["E_V"][0][i])
                        + "\t"
                        + str(new_data["E_V"][1][i])
                        + "\t"
                        + str(new_data["E_V"][2][i])
                        + "\t"
                        + str(new_data["E_V"][3][i])
                        + "\t"
                        + str(new_data["E_V"][4][i])
                        + "\t"
                        + str(new_data["E_V"][5][i])
                        + "\t"
                        + str(new_data["E_V"][6][i])
                        + "\t"
                        + str(new_data["E_V"][7][i])
                        + "\t"
                        + str(new_data["E_V"][8][i])
                    )
            except Exception:
                print(" ... canceling NImax IV stream")

        elif self.IO_estop and self.task_IV_run:
            dataI = self.task_CellCurrent.read(
                number_of_samples_per_channel=number_of_samples
            )
            dataV = self.task_CellVoltage.read(
                number_of_samples_per_channel=number_of_samples
            )
            self.task_CellCurrent.close()
            self.task_CellVoltage.close()

        else:
            # NImax has data but measurement was already turned off
            # just pull data from buffer and turn task off
            dataI = self.task_CellCurrent.read(
                number_of_samples_per_channel=number_of_samples
            )
            dataV = self.task_CellVoltage.read(
                number_of_samples_per_channel=number_of_samples
            )
            # task should be already off or should be closed soon
            print(" ... meas was turned off but NImax IV task is still running ...")
            # self.task_CellCurrent.close()
            # self.task_CellVoltage.close()

        return 0

    # # waits for TTL handshake, e.g. high signal
    # async def run_task_RSH_TTL_handshake(self):
    #     with nidaqmx.Task() as task_handshake:
    #         if 'port' in self.config_dict.dev_RSHTTLhandshake.keys() and 'term' in self.config_dict.dev_RSHTTLhandshake.keys():
    #             task_handshake.ci_channels.add_ci_count_edges_chan(self.config_dict.dev_RSHTTLhandshake['port'],
    #                                                                edge=Edge.RISING,
    #                                                                initial_count=0,
    #                                                                count_direction=CountDirection.COUNT_UP
    #                                                                )
    #             task_handshake.ci_channels[0].ci_count_edges_term = self.config_dict.dev_RSHTTLhandshake['term']

    #             # TODO: need to improve this once the real hardware is ready
    #             while True:
    #                 print(' ... waiting for RSH handshake ...')
    #                 data = task_handshake.read()
    #                 if data:
    #                     print(' ... got RSH handshake ...')
    #                     break
    #                 await asyncio.sleep(0.5)

    #             return {"name":"RSH_TTL_handshake",
    #                 "status": data
    #                }

    async def run_task_getFSW(self, FSW):
        with nidaqmx.Task() as task_FSW:
            if FSW in self.config_dict.dev_FSW.keys():
                task_FSW.di_channels.add_di_chan(
                    self.config_dict.dev_FSW[FSW],
                    line_grouping=LineGrouping.CHAN_PER_LINE,
                )
                data = task_FSW.read(number_of_samples_per_channel=1)
                return {"name": [FSW], "status": data}

    async def run_task_FSWBCD(self, BCDs, value):
        BCD_list = await self.sep_str(BCDs)
        cmds = []
        with nidaqmx.Task() as task_FSWBCD:
            for BCD in BCD_list:
                if BCD in self.config_dict.dev_FSWBCDCmd.keys():
                    task_FSWBCD.do_channels.add_do_chan(
                        self.config_dict.dev_FSWBCDCmd[BCD],
                        line_grouping=LineGrouping.CHAN_FOR_ALL_LINES,
                    )
                    cmds.append(value)
            if cmds:
                task_FSWBCD.write(cmds)
                return {"err_code": "0"}
            else:
                return {"err_code": "not found"}

    async def run_task_Pumps(self, pumps, value):
        print(" ... NIMAX pump:", pumps, value)
        pump_list = await self.sep_str(pumps)
        cmds = []
        with nidaqmx.Task() as task_Pumps:
            for pump in pump_list:
                if pump in self.config_dict.dev_Pumps.keys():
                    task_Pumps.do_channels.add_do_chan(
                        self.config_dict.dev_Pumps[pump],
                        line_grouping=LineGrouping.CHAN_FOR_ALL_LINES,
                    )
                    cmds.append(value)
            if cmds:
                task_Pumps.write(cmds)
                return {"err_code": "0"}
            else:
                return {"err_code": "not found"}

    async def run_task_GasFlowValves(self, valves, value):
        valve_list = await self.sep_str(valves)
        cmds = []
        with nidaqmx.Task() as task_GasFlowValves:
            for valve in valve_list:
                if valve in self.config_dict.dev_GasFlowValves.keys():
                    task_GasFlowValves.do_channels.add_do_chan(
                        self.config_dict.dev_GasFlowValves[valve],
                        line_grouping=LineGrouping.CHAN_FOR_ALL_LINES,
                    )
                    cmds.append(value)
            if cmds:
                task_GasFlowValves.write(cmds)
                return {"err_code": "0"}
            else:
                return {"err_code": "not found"}

    async def run_task_Master_Cell_Select(self, cells, value):
        cell_list = await self.sep_str(cells)
        if len(cell_list) > 1:
            print(
                " ... Multiple cell selected. Only one can be Master cell. Using first one!"
            )
            print(cell_list)
            cell_list = [cell_list[0]]
            print(cell_list)
        cmds = []
        with nidaqmx.Task() as task_MasterCell:
            for cell in cell_list:
                if cell in self.config_dict.dev_MasterCellSelect.keys():
                    task_MasterCell.do_channels.add_do_chan(
                        self.config_dict.dev_MasterCellSelect[cell],
                        line_grouping=LineGrouping.CHAN_FOR_ALL_LINES,
                    )
                    cmds.append(value)
            if cmds:
                task_MasterCell.write(cmds)
                return {"err_code": "0"}
            else:
                return {"err_code": "not found"}

    async def run_task_Active_Cells_Selection(self, cells, value):
        cell_list = await self.sep_str(cells)
        cmds = []
        with nidaqmx.Task() as task_ActiveCell:
            for cell in cell_list:
                if cell in self.config_dict.dev_ActiveCellsSelection.keys():
                    task_ActiveCell.do_channels.add_do_chan(
                        self.config_dict.dev_ActiveCellsSelection[cell],
                        line_grouping=LineGrouping.CHAN_FOR_ALL_LINES,
                    )
                    cmds.append(value)

                self.activeCell[int(cell) - 1] = value

            if self.qsettings.full():
                print(" ... NImax qsettings is full ...")
                _ = self.qsettings.get_nowait()
            self.qsettings.put_nowait({"activeCell": self.activeCell})

            if cmds:
                task_ActiveCell.write(cmds)
                return {"err_code": "0"}
            else:
                return {"err_code": "not found"}

    # TODO: test what happens if we clear all NIMax settings?
    async def run_task_Cell_IV(
        self, on, tstep=1.0,
    ):
        errcode = "Error"
        if not self.IO_estop:
            if on and not self.task_IV_run:

                ### save to file start settings
                self.FIFO_epoch = time.time_ns()
                self.FIFO_name = f'NImax_{time.strftime("%Y%m%d_%H%M%S%z.txt")}'
                self.FIFO_dir = self.local_data_dump
                # self.FIFO_dir = os.path.join(self.local_data_dump,action_params['save_folder'])
                print(" ... saving to:", self.FIFO_dir)
                # open new file and write header
                self.datafile.filename = self.FIFO_name
                self.datafile.filepath = self.FIFO_dir
                # if header is != '' then it will be written when file is opened first time
                # not if the file already exists
                # datafile.fileheader = ''
                self.datafile.open_file_sync()
                # ANEC2 will also measure more then one sample at a time, so we need to have a list of samples
                self.datafile.write_sampleinfo_sync(self.FIFO_sample)
                # NImax specific data
                # self.datafile.write_data_sync(self.FIFO_NImaxheader)
                self.datafile.write_data_sync("%epoch_ns=" + str(self.FIFO_epoch))
                self.datafile.write_data_sync("%version=0.1")
                self.datafile.write_data_sync(
                    "%column_headings=" + "\t".join(self.FIFO_column_headings)
                )
                ### save to file end settings

                self.create_IVtask(tstep)
                # start slave first
                self.task_CellVoltage.start()
                # then start master to trigger slave
                self.task_CellCurrent.start()
                self.task_IV_run = True
                errcode = 0

            elif not on and self.task_IV_run:
                self.task_IV_run = False
                #            self.task_CellCurrent.stop()
                #            self.task_CellVoltage.stop()
                self.task_CellCurrent.close()
                self.task_CellVoltage.close()
                # close file
                self.datafile.close_file_sync()

                await self.stat.set_idle()
                errcode = 0
        else:
            errcode = "estop"
            on = False
            await self.stat.set_estop()

        return {
            "meas": self.task_IV_run,
            "name": ["Cell_" + key for key in self.config_dict.dev_CellCurrent.keys()],
            "status": [on for _ in self.config_dict.dev_CellCurrent.keys()],
            "err_code": errcode,
            "datafile": os.path.join(self.FIFO_dir, self.FIFO_name),
        }

    ##########################################################################
    #  stops measurement, writes all data and returns from meas loop
    ##########################################################################
    async def stop(self):
        # turn off cell and run before stopping meas loop
        if self.task_IV_run:
            await self.run_task_Cell_IV(False)
            # file and Gamry connection will be closed with the meas loop
            self.task_IV_run = False
        else:
            # was already stopped so need to set to idle here
            await self.stat.set_idle()

    ##########################################################################
    #  same as estop, but also sets flag
    ##########################################################################
    async def estop(self, switch):
        # should be the same as stop()

        if self.task_IV_run:
            if switch:
                await self.stop()
            # will stop in 'stream_IV_callback
            self.IO_estop = switch
            await self.stat.set_estop()
        else:
            # was already stopped so need to set to idle here
            if switch:
                await self.stat.set_estop()
            else:
                await self.stat.set_idle()

    async def sep_str(self, cells):
        sepvals = [",", "\t", ";", "::", ":"]
        new_cells = None
        for sep in sepvals:
            if not (cells.find(sep) == -1):
                new_cells = cells.split(sep)
                break

        # single axis
        if new_cells == None:
            new_cells = cells

        # convert single axis move to list
        if type(new_cells) is not list:
            new_cells = [new_cells]

        return new_cells


################## END Helper functions #######################################
