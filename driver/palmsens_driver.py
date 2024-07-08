import os
import sys
from pathlib import Path
from typing import Callable, Union
import logging
from datetime import datetime
import clr
import json
import math
import queue
import time

helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'helper'))
from sdc_cyan import config as conf
from palmsems_helpers import saveToFile, loadVariable

## Imports from PalmsensSDK
import sys
sys.path.append(conf['palmsensDriver']["PalmsensSDK_python"])

from pspython.pspyinstruments import InstrumentManager, Instrument
#from pspython import pspymethods

# Add the dll file of the Palmsens SDK to import the required enums to make it work with Python >3.8
clr.AddReference(str(Path(conf['palmsensDriver']["PalmsensSDK_python"]).joinpath("pspython", "PalmSens.Core.dll")))
clr.AddReference(str(Path(conf['palmsensDriver']["PalmsensSDK_python"]).joinpath("pspython", "PalmSens.Core.Windows.dll")))
from System import Enum
from PalmSens.Techniques.Impedance import enumScanType, enumFrequencyType, EnumFrequencyMode
from PalmSens import CurrentRange, CurrentRanges
from PalmSens.Techniques import AmperometricDetection, ImpedimetricMethod, Potentiometry, OpenCircuitPotentiometry, LinearSweep, CyclicVoltammetry, MultiplePulseAmperometry, LinearSweepPotentiometry, DifferentialPulse, SquareWave, NormalPulse, Chronocoulometry, ImpedimetricGstatMethod

Path(f"{conf['palmsensDriver']['log_folder']}").joinpath("logs").mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s -%(name)s \n \t %(message)s \n",
    filename=str(Path(f"{conf['palmsensDriver']['log_folder']}").joinpath("logs", f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_logFile.log")),
    encoding="utf-8",
    force=True  # https://stackoverflow.com/questions/12158048/changing-loggings-basicconfig-which-is-already-set
    )

# create a logger for this module
logger_Palmsens_driver = logging.getLogger(f"run_logger.{__name__}")

class PalmsensDevice():
    """
    This class comprises the low level functionalities
    a Palmsens 4 device.
    """

    def __init__(self, callback_func: Callable = None) -> None:
        """
        This function initializes an instance of the PalmsensDevice class.

        Inputs:
        self: an instance of the PalmsensDevice class
        callback_func: a callback function, which is executed after every acquisition
            of a new datapoint.

        Outputs:
        This function has no outputs.
        """
        self.queue = queue.Queue()
        if callback_func is None:
            self.callback = self.default_callback
        else:
            self.callback = callback_func
        
        self.instrument_manager = InstrumentManager(new_data_callback=self.callback)
        self.instrument = None
        instrumentlist = self.find_instruments()
        self.connect(instrument=instrumentlist[-1])

    def default_callback(self, new_data):
        # Define what the default callback does
        for type, value in new_data.items():
                print(type + ' = ' + str(value))
        
        self.queue.put(new_data)
        logger_Palmsens_driver.info(f"Data received: {new_data}")
        return

    def find_instruments(self) -> list[Instrument]:
        """
        This function detects connected Palmsens devices.

        Inputs:
        self: an instance of the PalmsensDevice class

        Outputs:
        found_instruments: a list of instruments, which were detected
        """

        found_instruments = self.instrument_manager.discover_instruments()
        return found_instruments

    #def connect(self, instrument:Instrument) -> None:
    def connect(self, instrument:Instrument) -> None:
        """
        This function opens a connection to the given Palmsens device.

        Inputs:
        instrument: the Instrument object associated with the instrument to which the
        connection shall be established

        Outputs:
        This function has not outputs.
        """

        print(f"Connecting to instrument {instrument.name}.")
        status = self.instrument_manager.connect(instrument)
        if status==1:
            self.instrument = instrument
            logger_Palmsens_driver.info(f"Successfully connected to {instrument.name}.")
            print(f"Successfully connected to {instrument.name}.")
        else:
            raise ValueError(f"Connection to {instrument.name} failed.")

    def disconnect(self) -> None:
        """
        This function closes a connection to the Palmsens device associated with the
        respective instance of the PalmsensDevice class.

        Inputs:
        self: an instance of the PalmsensDevice class

        Outputs:
        This function has not outputs.
        """

        status = self.instrument_manager.disconnect()
        if status==1:
            logger_Palmsens_driver.info("Successfully disconnected "
                f"from {self.instrument.name}.")
            print(f"Successfully disconnected from {self.instrument.name}.")
        else:
            raise ValueError(f"Disconnecting from {self.instrument.name} failed.")

    def measure(
                self,
                method:str,
                parameters:dict,
                filename:str,
                save_folder:str=conf['palmsensDriver']["savepath_raw"]
               ) -> None:
        ''' This function performs a measurement in the defined method on the 
        Palmsens device. It saves the results to the path specified.
        Inputs:
        sampleName: a string defining the sample name to be used to label the sample
            for the measurement
        method: a string defining the method to be used as defined in the SDK of the
            device. Currently, this accepts "chronoamperometry" or
            "electrochemical_impedance_spectroscopy"
        parameters: a dictionary comrising the input parameters required to trigger the
            chosen method; the name of the parameter needs to be a string and be used as
            a key, while the parameter values are the values in the dictionary
        save_folder: The path to the folder, where the results shall be saved

        Outputs:
        This function has no outputs.
        '''
        # If an impedance measurement shall be made, transfer the parameters for the
        # scanType and the freqType to the relevant enums
        #if method == "electrochemical_impedance_spectroscopy":
        #    method_params = parameters

        #    for k in parameters.keys():
        #        if k == "scan_type":
        #            method_params[k] = enumScanType(parameters[k])
        #        elif k == "freq_type":
        #            method_params[k] = enumFrequencyType(parameters[k])
        #        else:
        #            method_params[k] = parameters[k]

        method_params = parameters

        # Select the requested method from the module
        method_callable = getattr(self, method)

        # Apply the parameters to the method
        method_parameterized = method_callable(**method_params)

        # Trigger the measurement
        result = self.instrument_manager.measure(method_parameterized)

        # Save the results
        save_folder = Path(save_folder)
        
        if not save_folder.resolve().exists():
            save_folder.mkdir(parents=True)
        
        saveToFile(
                   folder=str(save_folder),
                   #filename=f"{method}_{sampleName}",
                   filename=str(filename),
                   extension="json",
                   data=f"{str(result.__dict__)}"
                   )
        logger_Palmsens_driver.info(f"result:\n{str(result.__dict__)}")
        #print("Measurement finished \n"
        #     f"result:\n{str(result.__dict__)}")
        return result.__dict__

    def retrieveData(
                    self,
                    filename:str,
                    save_folder:str=conf['palmsensDriver']["savepath_raw"]
                    ) -> dict:
        ''' This function loads the data of a measurement and returns it as a dict. 
        Inputs:
        sampleName: a string defining the sample name to be used to label the sample
            for the measurement
        method: a string defining the method to be used as defined in the SDK of the
            device
        save_folder: The path to the folder, where the results shall be saved

        Outputs:
        loaded_result: the dictionary containing the results of a measruement
        '''

        # Load the results from the file
        #file_path = str(Path(save_folder).joinpath(f"{method}_{sampleName}.json"))
        #loaded_result = loadVariable(loadPath=file_path, variable="result")

        #file_path = Path(Path(save_folder).joinpath(f"{method}_{sampleName}.json"))
        file_path = Path(Path(save_folder).joinpath(f"{filename}.json"))
        print(file_path)
        logging.debug(f"Attempting to open file at path: {file_path}")
        if not file_path.exists():
            raise FileNotFoundError(f"No result file found for {filename} at {file_path}")

        return self.loadVariable(str(file_path))
    
    def loadVariable(self, loadPath):
        ''' Loads JSON data from the specified path. '''
        with open(loadPath, 'r', encoding='utf-8') as file:
            return json.load(file)
    
    ''' This part of the code is used to define the methods for the different electrochemical procedures
    '''
    def current_ranges(self, i_input: int) -> CurrentRange:
        if i_input == -1:
            i_applied = CurrentRange(CurrentRanges.cr100mA)
        elif i_input == -2:
            i_applied = CurrentRange(CurrentRanges.cr10mA)
        elif i_input == -3:
            i_applied = CurrentRange(CurrentRanges.cr1mA)
        elif i_input == -4:
            i_applied = CurrentRange(CurrentRanges.cr100uA)
        elif i_input == -5:
            i_applied = CurrentRange(CurrentRanges.cr10uA)
        elif i_input == -6:
            i_applied = CurrentRange(CurrentRanges.cr1uA)
        elif i_input == -7:
            i_applied = CurrentRange(CurrentRanges.cr100nA)
        elif i_input == -8:
            i_applied = CurrentRange(CurrentRanges.cr10nA)
        elif i_input == -9:
            i_applied = CurrentRange(CurrentRanges.cr1nA)
        return i_applied
    
    def convert_current_to_range(self, current):
        sign = -1 if current < 0 else 1
        magnitude = math.floor(math.log10(abs(current)))
        normalized_value = abs(current) * 10 ** -magnitude
        if normalized_value > 5:
            magnitude += 1
            normalized_value *= 0.1
        return sign * round(normalized_value, 1), magnitude
    
    def open_circuit_potentiometry(self, **kwargs):
        e_deposition = kwargs.get('e_deposition', 0.0) # DepositionPotential
        t_deposition = kwargs.get('t_deposition', 0.0) # DepositionTime
        e_conditioning = kwargs.get('e_conditioning', 0.0) # ConditioningPotential
        t_conditioning = kwargs.get('t_conditioning', 0.0) # ConditioningTime
        t_interval = kwargs.get('t_interval', 0.1) # IntervalTime
        t_run = kwargs.get('t_run', 1.0) # RunTime
        ocp = OpenCircuitPotentiometry()
        ocp.DepositionPotential = e_deposition
        ocp.DepositionTime = t_deposition
        ocp.ConditioningPotential = e_conditioning
        ocp.ConditioningTime = t_conditioning
        ocp.IntervalTime = t_interval
        ocp.RunTime = t_run
        return ocp

    def chronopotentiometry(self, **kwargs):
        e_deposition = kwargs.get('e_deposition', 0.0) # DepositionPotential
        t_deposition = kwargs.get('t_deposition', 0.0) # DepositionTime
        e_conditioning = kwargs.get('e_conditioning', 0.0) # ConditioningPotential
        t_conditioning = kwargs.get('t_conditioning', 0.0) # ConditioningTime
        i = kwargs.get('i', 1e-6) # Current in Amps
        i_value, i_range = self.convert_current_to_range(i) # Current in Amps to CurrentValue and CurrentRange
        i_applied = kwargs.get('i_applied', self.current_ranges(i_range)) # AppliedCurrentRange
        current = kwargs.get('current', i_value) # Current multiplied by current range, measured current is showed in uA
        t_interval = kwargs.get('t_interval', 0.2) # IntervalTime
        t_run = kwargs.get('t_run', 5.0) # RunTime
        e_max = kwargs.get('e_max', 0.5) # LimitMaxValue, should be 10 times smaller than actual value
        e_max_bool = kwargs.get('e_max_bool', False) # UseMaxValue
        e_min = kwargs.get('e_min', -0.5) # LimitMinValue, should be 10 times smaller than actual value
        e_min_bool = kwargs.get('e_min_bool', False) # UseMinValue
        #record_additional_data = 0 # ExtraValueMsk
        record_aux_input = kwargs.get('record_aux_input', False)
        record_we_potential = kwargs.get('record_we_potential', False)
        #if record_aux_input:
        #    record_additional_data += 16
        #if record_we_potential:
        #    record_additional_data += 2
        potentiometry = Potentiometry()
        potentiometry.DepositionPotential = e_deposition
        potentiometry.DepositionTime = t_deposition
        potentiometry.ConditioningPotential = e_conditioning
        potentiometry.ConditioningTime = t_conditioning
        potentiometry.AppliedCurrentRange = i_applied
        potentiometry.Current = current
        potentiometry.IntervalTime = t_interval
        potentiometry.RunTime = t_run
        potentiometry.LimitMaxValue = e_max
        potentiometry.LimitMinValue = e_min
        potentiometry.UseLimitMaxValue = e_max_bool
        potentiometry.UseLimitMinValue = e_min_bool
        #potentiometry.ExtraValueMsk = Enum(int(record_additional_data))
        return potentiometry
    
    def linear_sweep_potentiometry(self, **kwargs):
        e_deposition = kwargs.get('e_deposition', 0.0) # DepositionPotential
        t_deposition = kwargs.get('t_deposition', 0.0) # DepositionTime
        e_conditioning = kwargs.get('e_conditioning', 0.0) # ConditioningPotential
        t_conditioning = kwargs.get('t_conditioning', 0.0) # ConditioningTime
        i_input_range = int(kwargs.get('i_input_range', -6))
        i_applied = kwargs.get('i_applied', self.current_ranges(i_input_range))
        i_begin = kwargs.get('i_begin', -1.0) # BeginCurrent
        i_end = kwargs.get('i_end', 1.0) # EndCurrent
        i_step = kwargs.get('i_step', 0.01) # StepCurrent
        scan_rate = kwargs.get('scan_rate', 1.0) # ScanrateG **not a typo**
        lsp = LinearSweepPotentiometry()
        lsp.DepositionPotential = e_deposition
        lsp.DepositionTime = t_deposition
        lsp.ConditioningPotential = e_conditioning
        lsp.ConditioningTime = t_conditioning
        lsp.AppliedCurrentRange = i_applied
        lsp.BeginCurrent = i_begin
        lsp.EndCurrent = i_end
        lsp.StepCurrent = i_step
        lsp.ScanrateG = scan_rate
        return lsp
    
    def linear_sweep_voltammetry(self, **kwargs):
        e_deposition = kwargs.get('e_deposition', 0.0)
        t_deposition = kwargs.get('t_deposition', 0.0)
        e_conditioning = kwargs.get('e_conditioning', 0.0)
        t_conditioning = kwargs.get('t_conditioning', 0.0)
        equilibration_time = kwargs.get('equilibration_time', 2.0) # EquilibrationTime
        e_begin = kwargs.get('e_begin', -1.0) # BeginPotential
        e_end = kwargs.get('e_end', 1.0) # EndPotential
        e_step = kwargs.get('e_step', 0.01) # StepPotential
        scan_rate = kwargs.get('scan_rate', 1.0) # Scanrate
        record_additional_data = 0 # ExtraValueMsk
        record_aux_input = kwargs.get('record_aux_input', False)
        record_cell_potential = kwargs.get('record_cell_potential', False)
        record_we_potential = kwargs.get('record_we_potential', False)
        if record_aux_input:
            record_additional_data += 16
        if record_cell_potential:
            record_additional_data += 256
        if record_we_potential:
            record_additional_data += 2
        lsv = LinearSweep()
        lsv.DepositionPotential = e_deposition
        lsv.DepositionTime = t_deposition
        lsv.ConditioningPotential = e_conditioning
        lsv.ConditioningTime = t_conditioning
        lsv.EquilibrationTime = equilibration_time
        lsv.BeginPotential = e_begin
        lsv.EndPotential = e_end
        lsv.StepPotential = e_step
        lsv.Scanrate = scan_rate
        #lsv.ExtraValueMsk = Enum(int(record_additional_data))
        return lsv
    
    def cyclic_voltammetry(self, **kwargs):
        e_deposition = kwargs.get('e_deposition', 0.0) # DepositionPotential
        t_deposition = kwargs.get('t_deposition', 0.0) # DepositionTime
        e_conditioning = kwargs.get('e_conditioning', 0.0) # ConditioningPotential
        t_conditioning = kwargs.get('t_conditioning', 0.0) # ConditioningTime
        equilibration_time = kwargs.get('equilibration_time', 0) # EquilibrationTime
        e_begin = kwargs.get('e_begin', -0.5) # BeginPotential
        e_vtx1 = kwargs.get('e_vtx1', -1.0) # Vtx1Potential
        e_vtx2 = kwargs.get('e_vtx2', 1.0) # Vtx2Potential
        e_step = kwargs.get('e_step', 0.01) # StepPotential
        scan_rate = kwargs.get('scan_rate', 1.0) # Scanrate
        n_scans = kwargs.get('n_scans', 1) #nScans
        use_ir_drop_compensation = kwargs.get('use_ir_drop_compensation', False) # UseIRDropComp
        cv = CyclicVoltammetry()
        if use_ir_drop_compensation:
            ir_comp_resistance = kwargs.get('ir_comp_resistance', 0.0) # IRDropCompRes
            cv.UseIRDropComp = use_ir_drop_compensation
            cv.IRDropCompRes = ir_comp_resistance
        record_additional_data = 0 # ExtraValueMsk
        record_aux_input = kwargs.get('record_aux_input', False)
        record_cell_potential = kwargs.get('record_cell_potential', False)
        record_we_potential = kwargs.get('record_we_potential', False)
        if record_aux_input:
            record_additional_data += 16
        if record_cell_potential:
            record_additional_data += 256
        if record_we_potential:
            record_additional_data += 2
        cv.DepositionPotential = e_deposition
        cv.DepositionTime = t_deposition
        cv.ConditioningPotential = e_conditioning
        cv.ConditioningTime = t_conditioning
        cv.EquilibrationTime = equilibration_time
        cv.BeginPotential = e_begin
        cv.Vtx1Potential = e_vtx1
        cv.Vtx2Potential = e_vtx2
        cv.StepPotential = e_step
        cv.Scanrate = scan_rate
        cv.nScans = n_scans
        #cv.ExtraValueMsk = Enum(int(record_additional_data))
        return cv
    
    def chronoamperometry(self, **kwargs):
        e_deposition = kwargs.get('e_deposition', 0.0)
        t_deposition = kwargs.get('t_deposition', 0.0)
        e_conditioning = kwargs.get('e_conditioning', 0.0)
        t_conditioning = kwargs.get('t_conditioning', 0.0)
        equilibration_time = kwargs.get('equilibration_time', 0.0)
        interval_time = kwargs.get('interval_time', 0.1)
        e_applied = kwargs.get('e_applied', 0.0)
        run_time = kwargs.get('run_time', 1.0)
        record_additional_data = 0 # ExtraValueMsk
        record_aux_input = kwargs.get('record_aux_input', False)
        record_cell_potential = kwargs.get('record_cell_potential', False)
        record_we_potential = kwargs.get('record_we_potential', False)
        meas_vs_ocp_true = kwargs.get('meas_vs_ocp_true', 0) # OCPMode 1 = On, 0 = Off
        t_max_ocp = kwargs.get('t_max_ocp', 10.0) # OCPMaxOCPTime
        stability_criterion = kwargs.get('stability_criterion', 0.001) # OCPStabilityCriterion in mV/s
        i_max = kwargs.get('i_max', 0.0) # LimitMaxValue in uA
        i_max_bool = kwargs.get('i_max_bool', False) # UseMaxValue
        i_min = kwargs.get('i_min', 0.0) # LimitMinValue in uA
        i_min_bool = kwargs.get('i_min_bool', False) # UseMinValue
        use_ir_drop_compensation = kwargs.get('use_ir_drop_compensation', False) # UseIRDropComp
        if record_aux_input:
            record_additional_data += 16
        if record_cell_potential:
            record_additional_data += 256
        if record_we_potential:
            record_additional_data += 2
        ca = AmperometricDetection()
        if use_ir_drop_compensation:
            ir_comp_resistance = kwargs.get('ir_comp_resistance', 0.0) # IRDropCompRes
            ca.UseIRDropComp = use_ir_drop_compensation
            ca.IRDropCompRes = ir_comp_resistance
        ca.DepositionPotential = e_deposition
        ca.DepositionTime = t_deposition
        ca.ConditioningPotential = e_conditioning
        ca.ConditioningTime = t_conditioning
        ca.EquilibrationTime = equilibration_time
        ca.IntervalTime = interval_time
        ca.Potential = e_applied
        ca.RunTime = run_time
        ca.UseLimitMaxValue = i_max_bool
        ca.UseLimitMinValue = i_min_bool
        ca.LimitMaxValue = i_max
        ca.LimitMinValue = i_min
        ca.OCPMode = meas_vs_ocp_true
        ca.OCPMaxOCPTime = t_max_ocp
        ca.OCPStabilityCriterion = stability_criterion
        #ca.ExtraValueMsk = Enum(int(record_additional_data))
        return ca
    
    def multiple_pulse_amperometry(self, **kwargs):
        e_deposition = kwargs.get('e_deposition', 0.0) # DepositionPotential
        t_deposition = kwargs.get('t_deposition', 0.0) # DepositionTime
        e_conditioning = kwargs.get('e_conditioning', 0.0) # ConditioningPotential
        t_conditioning = kwargs.get('t_conditioning', 0.0) # ConditioningTime
        equilibration_time = kwargs.get('equilibration_time', 0) # EquilibrationTime
        e1 = kwargs.get("e1", 0.0) # E1
        e2 = kwargs.get("e2", 0.0) # E2
        e3 = kwargs.get("e3", 0.0) # E3
        t1 = kwargs.get("t1", 0.1) # t1
        t2 = kwargs.get("t2", 0.1) # t2
        t3 = kwargs.get("t3", 0.1) # t3
        run_time = kwargs.get("run_time", 10.0) # RunTime
        mpa = MultiplePulseAmperometry()
        mpa.DepositionPotential = e_deposition
        mpa.DepositionTime = t_deposition
        mpa.ConditioningPotential = e_conditioning
        mpa.ConditioningTIme = t_conditioning
        mpa.EquilibrationTime = equilibration_time
        mpa.E1 = e1
        mpa.E2 = e2
        mpa.E3 = e3
        mpa.t1 = t1
        mpa.t2 = t2
        mpa.t3 = t3
        mpa.RunTime = run_time
        return mpa
        
    def differential_pulse_voltammetry(self, **kwargs):
        e_deposition = kwargs.get('e_deposition', 0.0) # DepositionPotential
        t_deposition = kwargs.get('t_deposition', 0.0) # DepositionTime
        e_conditioning = kwargs.get('e_conditioning', 0.0) # ConditioningPotential
        t_conditioning = kwargs.get('t_conditioning', 0.0) # ConditioningTime
        equilibration_time = kwargs.get('equilibration_time', 0) # EquilibrationTime
        e_begin = kwargs.get("e_begin", -0.5) # BeginPotential
        e_end = kwargs.get('e_end', 0.5) # EndPotential
        e_step = kwargs.get('e_step', 0.01) # StepPotential
        scan_rate = kwargs.get('scan_rate', 0.1) # Scanrate
        e_pulse = kwargs.get('e_pulse', 0.2) # PulsePotential
        t_pulse = kwargs.get('t_pulse', 0.02) # PulseTime
        dpv = DifferentialPulse()
        dpv.DepositionPotential = e_deposition
        dpv.DepositionTIme = t_deposition
        dpv.ConditioningPotential = e_conditioning
        dpv.ConditioningTime = t_conditioning
        dpv.EquilibrationTime = equilibration_time
        dpv.BeginPotential = e_begin
        dpv.EndPotential = e_end
        dpv.StepPotential = e_step
        dpv.Scanrate = scan_rate
        dpv.PulsePotential = e_pulse
        dpv.PulseTime = t_pulse
        return dpv
    
    def square_wave_voltammetry(self, **kwargs):
        e_deposition = kwargs.get('e_deposition', 0.0) # DepositionPotential
        t_deposition = kwargs.get('t_deposition', 0.0) # DepositionTime
        e_conditioning = kwargs.get('e_conditioning', 0.0) # ConditioningPotential
        t_conditioning = kwargs.get('t_conditioning', 0.0) # ConditioningTime
        equilibration_time = kwargs.get('equilibration_time', 0) # EquilibrationTime
        e_begin = kwargs.get("e_begin", -0.25) # BeginPotential
        e_end = kwargs.get('e_end', 0.5) # EndPotential
        e_step = kwargs.get('e_step', 0.01) # StepPotential
        amplitude = kwargs.get('amplitude', 0.1) # PulseAmplitude
        frequency = kwargs.get('frequency', 20) # Frequency
        swv = SquareWave()
        swv.DepositionPotential = e_deposition
        swv.DepositionTime = t_deposition
        swv.ConditioningPotential = e_conditioning
        swv.ConditioningTime = t_conditioning
        swv.EquilibrationTime = equilibration_time
        swv.BeginPotential = e_begin
        swv.EndPotential = e_end
        swv.StepPotential = e_step
        swv.PulseAmplitude = amplitude
        swv.Frequency = frequency
        return swv
        
    def normal_wave_voltammetry(self, **kwargs):
        e_deposition = kwargs.get('e_deposition', 0.0) # DepositionPotential
        t_deposition = kwargs.get('t_deposition', 0.0) # DepositionTime
        e_conditioning = kwargs.get('e_conditioning', 0.0) # ConditioningPotential
        t_conditioning = kwargs.get('t_conditioning', 0.0) # ConditioningTime
        equilibration_time = kwargs.get('equilibration_time', 0) # EquilibrationTime
        e_begin = kwargs.get("e_begin", -0.5) # BeginPotential
        e_end = kwargs.get('e_end', 0.5) # EndPotential
        e_step = kwargs.get('e_step', 0.01) # StepPotential
        scan_rate = kwargs.get('scan_rate', 0.1) # Scanrate
        t_pulse = kwargs.get('t_pulse', 0.02) # PulseTime
        npv = NormalPulse()
        npv.DepositionPotential = e_deposition
        npv.DepositionTime = t_deposition
        npv.ConditioningPotential = e_conditioning
        npv.ConditioningTime = t_conditioning
        npv.EquilibrationTime = equilibration_time
        npv.BeginPotential = e_begin
        npv.EndPotential = e_end
        npv.StepPotential = e_step
        npv.Scanrate = scan_rate
        npv.PulseTime = t_pulse
        return npv
    
    def chronocoulometry(self, **kwargs):
        e_deposition = kwargs.get('e_deposition', 0.0) # DepositionPotential
        t_deposition = kwargs.get('t_deposition', 0.0) # DepositionTime
        e_conditioning = kwargs.get('e_conditioning', 0.0) # ConditioningPotential
        t_conditioning = kwargs.get('t_conditioning', 0.0) # ConditioningTime
        equilibration_time = kwargs.get('equilibration_time', 0) # EquilibrationTime
        interval_time = kwargs.get('interval_time', 0.1) # IntervalTime
        e_first_step = kwargs.get('e_step_1', 0.5) # EFirstStep
        e_second_step = kwargs.get('e_step_2', -0.5) # ESecondStep
        t_1 = kwargs.get('t_1', 5.0) #TFirstStep
        t_2 = kwargs.get('t_2', 5.0) #TSecondStep
        record_additional_data = 0 # ExtraValueMsk
        record_aux_input = kwargs.get('record_aux_input', False)
        record_cell_potential = kwargs.get('record_cell_potential', False)
        record_we_potential = kwargs.get('record_we_potential', False)
        if record_aux_input:
            record_additional_data += 16
        if record_cell_potential:
            record_additional_data += 256
        if record_we_potential:
            record_additional_data += 2
        chronocoulometry = Chronocoulometry()
        chronocoulometry.DepositionPotential = e_deposition
        chronocoulometry.DepositionTime = t_deposition
        chronocoulometry.ConditioningPotential = e_conditioning
        chronocoulometry.ConditioningTime = t_conditioning
        chronocoulometry.EquilibrationTime = equilibration_time
        chronocoulometry.IntervalTime = interval_time
        chronocoulometry.EFirstStep = e_first_step
        chronocoulometry.ESecondStep = e_second_step
        chronocoulometry.TFirstStep = t_1
        chronocoulometry.TSecondStep = t_2
        #chronocoulometry.ExtraValueMsk = Enum(int(record_additional_data))
        return chronocoulometry

    def potentiostatic_impedance_spectroscopy(self, **kwargs): 
        scan_type_ = kwargs.get('scan_type', 2)  # (0 = potential, 1 = time, 2 = fixed)
        if isinstance(scan_type_, int):
            scan_type = enumScanType(scan_type_)
        freq_type = kwargs.get('freq_type', 1)  # (0 = fixed, 1 = scan)
        if isinstance(freq_type, int):
            freq_type = enumFrequencyType(freq_type)
        equilibration_time = kwargs.get('equilibration_time', 0.0)
        e_dc = kwargs.get('e_dc', 0.0)
        e_ac = kwargs.get('e_ac', 0.01)
        n_frequencies = kwargs.get('n_frequencies', 10)
        max_frequency = kwargs.get('max_frequency', 1e5)
        min_frequency = kwargs.get('min_frequency', 1e4)
        meas_vs_ocp_true = kwargs.get('meas_vs_ocp_true', 1) # OCPMode 1 = On, 0 = Off
        t_max_ocp = kwargs.get('t_max_ocp', 1.0) # OCPMaxOCPTime
        stability_criterion = kwargs.get('stability_criterion', 0.001) # OCPStabilityCriterion in mV/s
        min_sampling_time = kwargs.get('sampling_time', 0.5) # SamplingTime
        max_equilibration_time = kwargs.get('max_equilibration_time', 5.0) # MaxEqTime
        record_aux_input = kwargs.get('record_aux_input', False) # ExtraValueMsk
        record_additional_data = 0
        if record_aux_input:
            record_additional_data += 16
        peis = ImpedimetricMethod()
        peis.ScanType = scan_type
        if scan_type_ == 2: # fixed
            e_dc = kwargs.get('e_dc', 0.0) # Edc (V)
            e_ac = kwargs.get('e_ac', 0.01) # Eac (V)
            peis.Potential = e_dc
            peis.Eac = e_ac
        elif scan_type_ == 1: # time scan
            e_dc = kwargs.get('e_dc', 0.0) # Edc (V)
            e_ac = kwargs.get('e_ac', 0.01) # Eac (V)
            t_interval = kwargs.get('t_interval', 0.01) # IntervalTime (s)
            t_run = kwargs.get('t_run', 1.0) # RunTime (s)
            peis.Potential = e_dc
            peis.Eac = e_ac
            peis.IntervalTime = t_interval
            peis.RunTime = t_run
        elif scan_type_ == 0: # potential scan
            e_begin = kwargs.get('e_begin', 0.0) # BeginPotential (V)
            e_step = kwargs.get('e_step', 0.1) # StepPotential (V)
            e_end = kwargs.get('e_end', 0.5) # EndPotential (V)
            e_ac = kwargs.get('e_ac', 0.01) # Eac (V)
            peis.BeginPotential = e_begin
            peis.StepPotential = e_step
            peis.EndPotential = e_end
            peis.Eac = e_ac
        peis.FreqType = freq_type
        peis.EquilibrationTime = equilibration_time
        peis.Potential = e_dc
        peis.Eac = e_ac
        peis.nFrequencies = n_frequencies
        peis.MaxFrequency = max_frequency
        peis.MinFrequency = min_frequency
        peis.OCPMode = meas_vs_ocp_true
        peis.OCPMaxOCPTime = t_max_ocp
        peis.OCPStabilityCriterion = stability_criterion
        peis.MaxEqTime = max_equilibration_time
        peis.SamplingTime = min_sampling_time
        #peis.ExtraValueMsk = Enum(int(record_additional_data))
        return peis
    
    def galvanostatic_impedance_spectroscopy(self, **kwargs):
        scan_type_ = kwargs.get('scan_type', 2)  # (0 = potential, 1 = time, 2 = fixed)
        if isinstance(scan_type_, int):
            scan_type = enumScanType(scan_type_)
        e_deposition = kwargs.get('e_deposition', 0.0) # DepositionPotential
        t_deposition = kwargs.get('t_deposition', 0.0) # DepositionTime
        e_conditioning = kwargs.get('e_conditioning', 0.0) # ConditioningPotential
        t_conditioning = kwargs.get('t_conditioning', 0.0) # ConditioningTime
        equilibration_time = kwargs.get('equilibration_time', 0) # EquilibrationTime
        i_input_range = int(kwargs.get('i_input_range', -6))
        i_applied = kwargs.get('i_applied', self.current_ranges(i_input_range)) # AppliedCurrentRange
        #i_ac = kwargs.get('i_ac', 0.01) # Iac
        #i_dc = kwargs.get('i_dc', 0.0) # Idc
        freq_type = kwargs.get('freq_type', 1)  # (0 = fixed, 1 = scan) FreqType
        if isinstance(freq_type, int):
            freq_type = enumFrequencyType(freq_type)
        n_frequencies = kwargs.get('n_frequencies', 41) # nFrequencies
        max_frequency = kwargs.get('max_frequency', 50000.0) # MaxFrequency
        min_frequency = kwargs.get('min_frequency', 5.0) # MinFrequency
        max_equilibration_time = kwargs.get('max_equilibration_time', 5.0) # MaxEqTime
        min_sampling_time = kwargs.get('sampling_time', 0.5) # SamplingTime
        record_aux_input = kwargs.get('record_aux_input', False) # ExtraValueMsk
        record_additional_data = 0
        if record_aux_input:
            record_additional_data += 16
        geis = ImpedimetricGstatMethod()
        geis.ScanType = scan_type
        if scan_type_ == 2: # fixed
            i_dc = kwargs.get('i_dc', 0.0) # Idc (*range)
            i_ac = kwargs.get('i_ac', 0.01) # Iac (*range)
            geis.Idc = i_dc
            geis.Iac = i_ac
        elif scan_type_ == 1: # time scan
            i_dc = kwargs.get('i_dc', 0.0) # Idc (*range)
            i_ac = kwargs.get('i_ac', 0.01) # Iac (*range)
            t_interval = kwargs.get('t_interval', 60.0) # IntervalTime (s)
            t_run = kwargs.get('t_run', 3600.0) # RunTime (s)
            geis.Idc = i_dc
            geis.Iac = i_ac
            geis.IntervalTime = t_interval
            geis.RunTime = t_run
        elif scan_type_ == 0: # current scan
            i_begin = kwargs.get('i_begin', 0.0) # BeginCurrent (*range)
            i_step = kwargs.get('i_step', 0.01) # StepCurrent (*range)
            i_end = kwargs.get('i_end', 0.0) # EndCurrent (V)
            i_ac = kwargs.get('i_ac', 0.01) # Iac (V)
            geis.BeginCurrent = i_begin
            geis.StepCurrent = i_step
            geis.EndCurrent = i_end
            geis.Iac = i_ac
        geis.DepositionPotential = e_deposition
        geis.DepositionTime = t_deposition
        geis.ConditioningPotential = e_conditioning
        geis.ConditioningTime = t_conditioning
        geis.EquilibrationTime = equilibration_time
        geis.AppliedCurrentRange = i_applied
        geis.ScanType = scan_type
        #geis.Iac = i_ac
        #geis.Idc = i_dc
        geis.FreqType = freq_type
        geis.nFrequencies = n_frequencies
        geis.MaxFrequency = max_frequency
        geis.MinFrequency = min_frequency
        geis.MaxEqTime = max_equilibration_time
        geis.SamplingTime = min_sampling_time
        #geis.ExtraValueMsk = Enum(int(record_additional_data))
        return geis
