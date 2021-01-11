""" A device class for the Galil motion controller, used by a FastAPI server instance.

The 'galil' device class exposes motion and I/O functions from the underlying 'gclib'
library. Class methods are specific to Galil devices. Device configuration is read from
config/config.py. 
"""

#import sys
#import os
import numpy as np
import json
import time

# if __package__:
#     # can import directly in package mode
#     print("importing config vars from package path")
# else:
#     # interactive kernel mode requires path manipulation
#     cwd = os.getcwd()
#     pwd = os.path.dirname(cwd)
#     if os.path.basename(pwd) == "helao-dev":
#         sys.path.insert(0, pwd)
#     if pwd in sys.path or os.path.basename(cwd) == "helao-dev":
#         print("importing config vars from sys.path")
#     else:
#         raise ModuleNotFoundError("unable to find config vars, current working directory is {}".format(cwd))


# install galil driver first
# (helao) c:\Program Files (x86)\Galil\gclib\source\wrappers\python>python setup.py install
import gclib

class cmd_exception(ValueError):
    def __init__(self, arg):
        self.args = arg


class galil:
    def __init__(self, config_dict):
        self.config_dict = config_dict

        self.config_dict["estop_motor"] = False
        self.config_dict["estop_io"] = False

        # if this is the main instance let us make a galil connection
        self.g = gclib.py()
        print("gclib version:", self.g.GVersion())
        self.g.GOpen("%s --direct -s ALL" % (self.config_dict["galil_ip_str"]))
        print(self.g.GInfo())
        self.c = self.g.GCommand  # alias the command callable
        self.cycle_lights = False


    def motor_move(self, multi_x_mm, multi_axis, speed, mode):
        stopping=False # no stopping of any movement by other actions
        # this function moves the motor by a set amount of milimeters
        # you have to specify the axis,
        # if no axis is specified this function throws an error
        # if no speed is specified we use the default slow speed
        # as specified in the setupdict

        # example: move the motor 5mm to the positive direction:
        # motor_move(5,'x')
        # example: move the motor to absolute 0 mm
        # motor_move(5,'x',mode='absolute')
        # home the motor at low speed (the distance is not used)
        # motor_move(5,'x',mode='homing',speed=10000)
        # multi axis move:
        # motor_move([5, 10],['x', 'y'],mode='absolute',speed=10000)
        # the server call would look like:
        # http://127.0.0.1:8001/motor/set/move?x_mm=-20&axis=x&mode=relative
        # http://127.0.0.1:8001/motor/set/move?x_mm=-20&axis=x&mode=absolute


        # convert single axis move to list    
        if type(multi_x_mm) is not list:
            multi_axis = [multi_axis]
            multi_x_mm = [multi_x_mm]
        
        # return value arrays for multi axis movement
        ret_moved_axis = []
        ret_speed = []
        ret_accepted_rel_dist = []
        ret_supplied_rel_dist = []
        ret_err_dist = []
        ret_err_code = []
        ret_counts = []
        
        # expected time for each move, used for axis stop check
        timeofmove = []
        
        # TODO: if same axis is moved twice
        for x_mm, axis in zip(multi_x_mm, multi_axis):
            # need to remove stopping for multi-axis move
            if len(ret_moved_axis) > 0:
                stopping = False


            # first we check if we have the right axis specified
            if axis in self.config_dict["axis_id"].keys():
                ax = self.config_dict["axis_id"][axis]
            else:
                ret_moved_axis.append(None)
                ret_speed.append(None)
                ret_accepted_rel_dist.append(None)
                ret_supplied_rel_dist.append(x_mm)
                ret_err_dist.append(None)
                ret_err_code.append("setup")
                ret_counts.append(None)
                continue
    
            # check if the motors are moving if so return an error message
            # recalculate the distance in mm into distance in counts
            try:
                print(self.config_dict["count_to_mm"][ax])
                float_counts = (
                    x_mm / self.config_dict["count_to_mm"][ax]
                )  # calculate float dist from steupd
                print(self.config_dict["count_to_mm"][ax])
    
                counts = int(np.floor(float_counts))  # we can only mode full counts
                # save and report the error distance
                error_distance = self.config_dict["count_to_mm"][ax] * (float_counts - counts)
    
                # check if a speed was upplied otherwise set it to standart
                if speed == None:
                    speed = self.config_dict["def_speed_count_sec"]
                else:
                    speed = int(np.floor(speed))
    
                if speed > self.config_dict["max_speed_count_sec"]:
                    speed = self.config_dict["max_speed_count_sec"]
                self._speed = speed
            except:
                # something went wrong in the numerical part so we give that as feedback
                ret_moved_axis.append(None)
                ret_speed.append(None)
                ret_accepted_rel_dist.append(None)
                ret_supplied_rel_dist.append(x_mm)
                ret_err_dist.append(None)
                ret_err_code.append("numerical")
                ret_counts.append(None)
                continue
            try:
                # the logic here is that we assemble a command sequence
                # here we decide if we move relative, home, or move absolute
                if mode not in ["relative", "absolute", "homing"]:
                    raise cmd_exception
                if stopping:
                    #cmd_seq = ["AB", "MO{}".format(ax), "SH{}".format(ax), "SP{}={}".format(ax, speed)]
                    cmd_seq = ["ST {}".format(ax), "MO{}".format(ax), "SH{}".format(ax), "SP{}={}".format(ax, speed)]
                else:
                    cmd_seq = ["SP{}={}".format(ax, speed)]
                if mode == "relative":
                    cmd_seq.append("PR{}={}".format(ax, counts))
                if mode == "homing":
                    cmd_seq.append("HM{}".format(ax))
                if mode == "absolute":
                    # now we want an abolute position
                    cmd_seq.append("PA{}={}".format(ax, counts))
                cmd_seq.append("BG{}".format(ax))
    
                #ret = ""
                for cmd in cmd_seq:
                    _ = self.c(cmd)
                    #ret.join(_)
                ret_moved_axis.append(ax)
                ret_speed.append(speed)
                ret_accepted_rel_dist.append(None)
                ret_supplied_rel_dist.append(x_mm)
                ret_err_dist.append(error_distance)
                ret_err_code.append(0)
                ret_counts.append(counts)
                # time = counts/ counts_per_second
                timeofmove.append(counts/speed)
                continue
            except:
                ret_moved_axis.append(None)
                ret_speed.append(None)
                ret_accepted_rel_dist.append(None)
                ret_supplied_rel_dist.append(x_mm)
                ret_err_dist.append(None)
                ret_err_code.append("motor")
                ret_counts.append(None)
                continue


        # get max time until all axis are expected to have stopped
        if len(timeofmove)>0:
            tmax = max(timeofmove)
            if tmax > 30*60:
                tmax > 30*60 # 30min hard limit
        else:
            tmax = 0
        
        # wait for expected axis move time before checking if axis stoppped
        print('Axis expected to stop in',tmax,'sec')
        time.sleep(tmax)        

        # check if all axis stopped
        tstart = time.time()
        if "timeout" in self.config_dict:
            tout = self.config_dict["timeout"]
        else:
            tout = 60
        while time.time()-tstart < tout:
            rettmp = self.query_axis_moving(multi_axis)
            time.sleep(0.5) # TODO: what time is ok to wait and not to overload the Galil
#            print(rettmp)
            if all(rettmp['err_code']):
#                print('Motors stopped')
                break
#            else:
#                print('Motors moving')
 
        # Estop of motor movement (motor still on)
        if time.time()-tstart > tout:
            self.stop_axis(multi_axis)

        # one return for all axis 
        return {
            "moved_axis": ret_moved_axis,
            "speed": ret_speed,
            "accepted_rel_dist": ret_accepted_rel_dist,
            "supplied_rel_dist": ret_supplied_rel_dist,
            "err_dist": ret_err_dist,
            "err_code": ret_err_code,
            "counts": ret_counts
        }


    def motor_move_live(self, x_mm, axis, speed, mode):
        # this function moves the motor by a set amount of milimeters
        # you have to specify the axis,
        # if no axis is specified this function throws an error
        # if no speed is specified we use the default slow speed
        # as specified in the setupdictm

        # example: move the motor 5mm to the positive direction:
        # motor_move(5,'x')
        # example: move the motor to absolute 0 mm
        # motor_move(5,'x',mode='absolute')
        # home the motor at low speed (the distance is not used)
        # motor_move(5,'x',mode='homing',speed=10000)
        # the server call would look like:
        # http://127.0.0.1:8001/motor/set/move?x_mm=-20&axis=x&mode=relative
        # http://127.0.0.1:8001/motor/set/move?x_mm=-20&axis=x&mode=absolute

        # first we check if we have the right axis specified
        if axis in self.config_dict["axis_id"].keys():
            ax = self.config_dict["axis_id"][axis]
        else:
            return {
                "moved_axis": None,
                "speed": None,
                "accepted_rel_dist": None,
                "supplied_rel_dist": x_mm,
                "err_dist": None,
                "err_code": "setup",
            }

        # check if the motors are moving if so return an error message
        # recalculate the distance in mm into distance in counts
        try:
            float_counts = (
                x_mm / self.config_dict["count_to_mm"][ax]
            )  # calculate float dist from steupd
            counts = int(np.floor(float_counts))  # we can only mode full counts
            # save and report the error distance
            error_distance = self.config_dict["count_to_mm"][ax] * (float_counts - counts)

            # check if a speed was upplied otherwise set it to standart
            if speed == None:
                speed = self.config_dict["def_speed_count_sec"]
            else:
                speed = int(np.floor(speed))

            if speed > self.config_dict["max_speed_count_sec"]:
                speed = self.config_dict["max_speed_count_sec"]
            self._speed = speed
        except:
            # something went wrong in the numerical part so we give that as feedback
            return {
                "moved_axis": None,
                "speed": None,
                "accepted_rel_dist": None,
                "supplied_rel_dist": x_mm,
                "err_dist": None,
                "err_code": "numerical",
            }
        try:
            # the logic here is that we assemble a command sequence
            # here we decide if we move relative, home, or move absolute
            if mode not in ["relative", "absolute", "homing"]:
                raise cmd_exception

            # stops all other motion
            #cmd_seq = ["AB", "MO{}".format(ax), "SH{}".format(ax), "SP{}={}".format(ax, speed)]
            #cmd_seq = ["ST {}".format(ax), "MO{}".format(ax), "SH{}".format(ax), "SP{}={}".format(ax, speed)]
            # other motion won't be affected
            cmd_seq = ["SP{}={}".format(ax, speed)]
            if mode == "relative":
                cmd_seq.append("PR{}={}".format(ax, counts))
            if mode == "homing":
                cmd_seq.append("HM{}".format(ax))
            if mode == "absolute":
                # now we want an abolute position
                cmd_seq.append("PA{}={}".format(ax, counts))
            cmd_seq.append("BG{}".format(ax))

            ret = ""
            for cmd in cmd_seq:
                _ = self.c(cmd)
                ret.join(_)
            while self.query_axis_moving(axis)["motor_status"] == ["moving"]:
                d = {
                    "moved_axis": ax,
                    "speed": speed,
                    "accepted_rel_dist": None,
                    "supplied_rel_dist": x_mm,
                    "err_dist": error_distance,
                    "err_code": 0,
                    "position": self.query_axis_position(ax),
                }
                d = json.dumps(d)
                yield d
            d = {
                "moved_axis": ax,
                "speed": speed,
                "accepted_rel_dist": None,
                "supplied_rel_dist": x_mm,
                "err_dist": error_distance,
                "err_code": 0,
                "position": self.query_axis_position(ax),
            }
            d = json.dumps(d)
            yield d
        except:
            d = {
                "moved_axis": ax,
                "speed": speed,
                "accepted_rel_dist": None,
                "supplied_rel_dist": x_mm,
                "err_dist": error_distance,
                "err_code": 0,
                "position": self.query_axis_position(ax),
            }
            d = json.dumps(d)
            yield d


    def motor_disconnect(self):
        try:
            self.g.GClose()  # don't forget to close connections!
        except gclib.GclibError as e:
            return {"connection": {"Unexpected GclibError:", e}}
        return {"connection": "motor_offline"}


    def query_axis_position(self, multi_axis):
        # this only queries the position of a single axis
        # server example:
        # http://127.0.0.1:8000/motor/query/position?axis=x
        
        # convert single axis move to list
        if type(multi_axis) is not list:
            multi_axis = [multi_axis]

        q = self.c("TP")  # query position of all axis
        # now we need to map these outputs to the ABCDEFG... channels
        # and then map that to xyz so it is humanly readable
        axlett = 'ABCDEFGH'
        axlett[0:len(q.split(', '))]
        inv_axis_id = {d: v for v, d in self.config_dict["axis_id"].items()}
        ax_abc_to_xyz = {l: inv_axis_id[l] for i, l in enumerate(axlett)}
        pos = {
            axl: int(r) * self.config_dict["count_to_mm"][axl]
            for axl, r in zip(axlett, q.split(", "))
        }
        # return the results through calculating things into mm
        axpos = {ax_abc_to_xyz[k]: p for k, p in pos.items()}

        ret_ax = []
        ret_position = []
        for axis in multi_axis:
            if axis in axpos.keys():
                ret_ax.append(axis)
                ret_position.append(axpos[axis])
            else:
                ret_ax.append(None)
                ret_position.append(None)

        return {"ax": ret_ax, "position": ret_position}


    def query_axis_moving(self, multi_axis):
        # this functions queries the status of the axis
        q = self.c("SC")
        axlett = 'ABCDEFGH'
        axlett[0:len(q.split(', '))]
        # convert single axis move to list
        if type(multi_axis) is not list:
            multi_axis = [multi_axis]
        ret_status = []
        ret_err_code = []
        for axis in multi_axis:
            for axl, r in zip(axlett, q.split(", ")):
                if int(r) == 0:
                    ret_status.append("moving")
                    ret_err_code.append(int(r))
                elif int(r) == 1:
                    ret_status.append("stopped")
                    ret_err_code.append(int(r))
                else:
                    # stopped due to error/issue
                    ret_status.append("stopped")
                    ret_err_code.append(int(r))
        return {
            "motor_status": ret_status,
            "err_code": ret_err_code
        }


    def stop_axis(self, multi_axis):
        # this will stop the current motion of the axis
        # but not turn off the motor
        # for stopping and turnuing off use moto_off

        # convert single axis move to list
        if type(multi_axis) is not list:
            multi_axis = [multi_axis]
        for axis in multi_axis:
            if axis in self.config_dict["axis_id"].keys():
                ax = self.config_dict["axis_id"][axis]
                self.c("ST {}".format(ax))

        ret = self.query_axis_moving(multi_axis)
        ret.update(self.query_axis_position(multi_axis))
        return ret


    def motor_off(self, multi_axis):
        
        # sometimes it is useful to turn the motors off for manual alignment
        # this function does exactly that
        # It then returns the status
        # and the current position of all motors

        # an example would be:
        # http://127.0.0.1:8000/motor/stop
        # convert single axis move to list
        if type(multi_axis) is not list:
            multi_axis = [multi_axis]

        for axis in multi_axis:

            if axis in self.config_dict["axis_id"].keys():
                ax = self.config_dict["axis_id"][axis]
            else:
                continue
                #ret = self.query_axis_moving(multi_axis)
                #ret.update(self.query_axis_position(multi_axis))
                #return ret
    
            #cmd_seq = ["AB", "MO{}".format(ax)]
            cmd_seq = ["ST {}".format(ax), "MO{}".format(ax)]
            
            for cmd in cmd_seq:
                _ = self.c(cmd)


        ret = self.query_axis_moving(multi_axis)
        ret.update(self.query_axis_position(multi_axis))
        return ret


    def motor_on(self, multi_axis):
        # sometimes it is useful to turn the motors back on for manual alignment
        # this function does exactly that
        # It then returns the status
        # and the current position of all motors
        # server example
        # http://127.0.0.1:8000/motor/on?axis=x

        # convert single axis move to list
        if type(multi_axis) is not list:
            multi_axis = [multi_axis]

        for axis in multi_axis:

            if axis in self.config_dict["axis_id"].keys():
                ax = self.config_dict["axis_id"][axis]
            else:
                continue
                #ret = self.query_axis_moving(multi_axis)
                #ret.update(self.query_axis_position(multi_axis))
                #return ret
            #cmd_seq = ["AB", "SH{}".format(ax)]
            cmd_seq = ["ST {}".format(ax), "SH{}".format(ax)]
            
            for cmd in cmd_seq:
                _ = self.c(cmd)

        ret = self.query_axis_moving(multi_axis)
        ret.update(self.query_axis_position(multi_axis))
        return ret


    def read_analog_in(self, multi_port):
        # this reads the value of an analog in port
        # http://127.0.0.1:8000/
        if type(multi_port) is not list:
            multi_port = [multi_port]
        ret = []
        for port in multi_port:        
            ret.append(self.c("MG @AN[{}]".format(int(port))))
        return {"port": port, "value": ret, "type": "analog_in"}


    def read_digital_in(self, multi_port):
        # this reads the value of a digital in port
        # http://127.0.0.1:8000/
        if type(multi_port) is not list:
            multi_port = [multi_port]
        ret = []
        for port in multi_port:        
            ret.append(self.c("MG @IN[{}]".format(int(port))))
        return {"port": multi_port, "value": ret, "type": "digital_in"}


    def read_digital_out(self, multi_port):
        # this reads the value of an digital out port i.e. what is
        # actuallybeing put out (for checking)
        # http://127.0.0.1:8000/
        if type(multi_port) is not list:
            multi_port = [multi_port]
        ret = []
        for port in multi_port:        
            ret.append(self.c("MG @IN[{}]".format(int(port))))
        return {"port": multi_port, "value": ret, "type": "digital_out"}


    def set_analog_out(self, multi_port, handle: int, module: int, bitnum: int, multi_value):
        # this is essentially a placeholder for now since the DMC-4143 does not support
        # analog out but I believe it is worthwhile to have this in here for the RIO
        # Handle num is A-H and must be on port 502 for the modbus commons
        # module is the position of the module from 1 to 16
        # bitnum is the IO point in the module from 1-4
        # the fist value n_0
        #n_0 = handle * 1000 + (module - 1) * 4 + bitnum
        #_ = self.c("AO {},{}".format(port, value))
        return {"port": multi_port, "value": multi_value, "type": "analog_out"}


    def digital_out_on(self, multi_port):
        if type(multi_port) is not list:
            multi_port = [multi_port]
        for port in multi_port:        
            _ = self.c("SB {}".format(int(port)))
        return {
            "port": multi_port,
            "value": self.read_digital_out(multi_port),
            "type": "digital_out",
        }


    def digital_out_off(self, multi_port):
        if type(multi_port) is not list:
            multi_port = [multi_port]

        for port in multi_port:
            _ = self.c("CB {}".format(int(port)))

        return {
            "port": multi_port,
            "value": self.read_digital_out(multi_port),
            "type": "digital_out",
        }


    def infinite_digital_cycles(self, on_time=0.2, off_time=0.2, port=0, init_time=0):
        self.cycle_lights = True
        time.sleep(init_time)
        while self.cycle_lights:
            self.digital_out_on(port)
            time.sleep(on_time)
            self.digital_out_off(port)
            time.sleep(off_time)
        return {
            "port": port,
            "value": "ran_infinite_light_cycles",
            "type": "digital_out",
        }


    def break_infinite_digital_cycles(
        self, on_time=0.2, off_time=0.2, port=0, init_time=0
    ):
        self.cycle_lights = False


    def get_all_axis(self):
        return [axis for axis in self.config_dict["axis_id"].keys()]
        

    def shutdown_event(self):
        # this gets called when the server is shut down or reloaded to ensure a clean
        # disconnect ... just restart or terminate the server
        #self.stop_axis(self.get_all_axis())
        self.motor_off(self.get_all_axis()) # already contains stop command
        self.g.GClose()
        return {"shutdown"}
