""" schemas.py
Standard classes for experiment queue objects.

"""
from collections import defaultdict
from datetime import datetime
from typing import Optional, Union
import types

import numpy as np

from helao.core.helper import gen_uuid
from helao.core.model import return_finishedact, return_runningact


class Decision(object):
    "Sample-process grouping class."

    def __init__(
        self,
        inputdict: Optional[dict] = None,
        orch_name: str = "orchestrator",
        technique_name: str = None,
        decision_label: str = "nolabel",
        actualizer: str = None,
        actual_pars: dict = {},
        result_dict: dict = {},
        access: str = "hte",
    ):
        imports = {}
        if inputdict:
            imports.update(inputdict)
        self.orch_name = imports.get("orch_name", orch_name)
        self.technique_name = imports.get("technique_name", technique_name)
        self.decision_uuid = imports.get("decision_uuid", None)
        self.decision_timestamp = imports.get("decision_timestamp", None)
        self.decision_label = imports.get("decision_label", decision_label)
        self.access = imports.get("access", access)
        self.actual = imports.get("actual", actualizer)
        self.actual_pars = imports.get("actual_pars", actual_pars)
        self.result_dict = imports.get("result_dict", result_dict)
        if self.decision_uuid is None:
            self.gen_uuid_decision()

    def as_dict(self):
        d = vars(self)
        attr_only = {
            k: v
            for k, v in d.items()
            if type(v) != types.FunctionType and not k.startswith("__")
        }
        return attr_only

    def gen_uuid_decision(self):
        "server_name can be any string used in generating random uuid"
        if self.decision_uuid:
            print(f"decision_uuid: {self.decision_uuid} already exists")
        else:
            self.decision_uuid = gen_uuid(self.orch_name)
            print(f"decision_uuid: {self.decision_uuid} assigned")

    def set_dtime(self, offset: float = 0):
        dtime = datetime.now()
        dtime = datetime.fromtimestamp(dtime.timestamp() + offset)
        self.decision_timestamp = dtime.strftime("%Y%m%d.%H%M%S%f")


class Action(Decision):
    "Sample-process identifier class."

    def __init__(
        self,
        inputdict: Optional[dict] = None,
        action_server: str = None,
        action_name: str = None,
        action_params: dict = {},
        action_enum: str = None,
        action_abbr: str = None,
        save_rcp: bool = False,
        save_data: Union[bool, int, str] = None,
        start_condition: Union[int, dict] = 3,
        plate_id: Optional[int] = None,
        samples_in: Optional[dict] = None,
        # samples_out: Optional[dict] = None,
    ):
        super().__init__(inputdict)  # grab decision keys
        imports = {}
        if inputdict:
            imports.update(inputdict)
        self.action_uuid = imports.get("action_uuid", None)
        self.action_queue_time = imports.get("action_queue_time", None)
        self.action_server = imports.get("action_server", action_server)
        self.action_name = imports.get("action_name", action_name)
        self.action_params = imports.get("action_params", action_params)
        self.action_enum = imports.get("action_enum", action_enum)
        self.action_abbr = imports.get("action_abbr", action_abbr)
        self.save_rcp = imports.get("save_rcp", save_rcp)
        self.save_data = imports.get("save_data", save_data)
        self.start_condition = imports.get("start_condition", start_condition)
        self.plate_id = imports.get("plate_id", plate_id)
        self.samples_in = imports.get("samples_in", samples_in)
        # the following attributes are set during Action dispatch but can be imported
        self.samples_out = imports.get("samples_out", None)
        self.file_dict = defaultdict(lambda: defaultdict(dict))
        self.file_dict.update(imports.get("file_dict", {}))
        self.file_paths = imports.get("file_paths", [])
        self.data = imports.get("data", [])
        self.output_dir = imports.get("output_dir", None)
        self.column_names = imports.get("column_names", None)
        self.header = imports.get("header", None)
        self.file_type = imports.get("file_type", None)
        self.filename = imports.get("filename", None)
        self.file_group = imports.get("file_group", None)

        check_args = {"server": self.action_server, "name": self.action_name}
        missing_args = [k for k, v in check_args.items() if v is None]
        if missing_args:
            print(
                f'Action {" and ".join(missing_args)} not specified. Placeholder actions will only affect the action queue enumeration.'
            )
        if self.action_uuid is None:
            self.gen_uuid_action()

    def gen_uuid_action(self):
        if self.action_uuid:
            print(f"action_uuid: {self.action_uuid} already exists")
        else:
            self.action_uuid = gen_uuid(self.action_name)
            print(f"action_uuid: {self.action_uuid} assigned")

    def set_atime(self, offset: float = 0.0):
        atime = datetime.now()
        if offset is not None:
            atime = datetime.fromtimestamp(atime.timestamp() + offset)
        self.action_queue_time = atime.strftime("%Y%m%d.%H%M%S%f")

    def return_finished(self):
        return return_finishedact(
            technique_name=self.technique_name,
            access=self.access,
            orch_name=self.orch_name,
            decision_timestamp=self.decision_timestamp,
            decision_uuid=self.decision_uuid,
            decision_label=self.decision_label,
            actualizer=self.actualizer,
            actual_pars=self.actual_pars,
            result_dict=self.result_dict,
            action_server=self.action_server,
            action_queue_time=self.action_queue_time,
            action_real_time=self.action_real_time,
            action_name=self.action_name,
            action_params=self.action_params,
            action_uuid=self.action_uuid,
            action_enum=self.action_enum,
            action_abbr=self.action_abbr,
            actionnum=self.actionnum,
            start_condition=self.start_condition,
            save_rcp=self.save_rcp,
            save_data=self.save_data,
            plate_id=self.plate_id,
            samples_in=self.samples_in,
            samples_out=self.samples_out,
            output_dir=self.output_dir,
            file_dict=self.file_dict,
            column_names=self.column_names,
            header=self.header,
            data=self.data,
        )

    def return_running(self):
        return return_runningact(
            technique_name=self.technique_name,
            access=self.access,
            orch_name=self.orch_name,
            decision_timestamp=self.decision_timestamp,
            decision_uuid=self.decision_uuid,
            decision_label=self.decision_label,
            actualizer=self.actualizer,
            actual_pars=self.actual_pars,
            result_dict=self.result_dict,
            action_server=self.action_server,
            action_queue_time=self.action_queue_time,
            action_real_time=self.action_real_time,
            action_name=self.action_name,
            action_params=self.action_params,
            action_uuid=self.action_uuid,
            action_enum=self.action_enum,
            action_abbr=self.action_abbr,
            actionnum=self.actionnum,
            start_condition=self.start_condition,
            plate_id=self.plate_id,
            save_rcp=self.save_rcp,
            save_data=self.save_data,
            samples_in=self.samples_in,
            samples_out=self.samples_out,
            output_dir=self.output_dir,
        )


class transformxy:
    # Updating plate calibration will automatically update the system transformation
    # matrix. When angles are changed updated them also here and run update_Msystem
    def __init__(self, Minstr, seq=None):
        # instrument specific matrix
        # motor to instrument
        self.Minstrxyz = np.asmatrix(Minstr)  # np.asmatrix(np.identity(4))
        self.Minstr = np.asmatrix(np.identity(4))
        self.Minstrinv = np.asmatrix(np.identity(4))
        # plate Matrix
        # instrument to plate
        self.Mplate = np.asmatrix(np.identity(4))
        self.Mplatexy = np.asmatrix(np.identity(3))
        # system Matrix
        # motor to plate
        self.M = np.asmatrix(np.identity(4))
        self.Minv = np.asmatrix(np.identity(4))
        # need to update the angles here each time the axis is rotated
        self.alpha = 0
        self.beta = 0
        self.gamma = 0
        self.seq = seq

        # pre calculates the system Matrix M
        self.update_Msystem()
        print(" ... Minstr", self.Minstr)
        print(" ... Minstrxyz", self.Minstrxyz)

    def transform_platexy_to_motorxy(self, platexy):
        """simply calculates motorxy based on platexy
        plate warping (z) will be a different call"""
        platexy = np.asarray(platexy)
        if len(platexy) == 3:
            platexy = np.insert(platexy, 2, 0)
        # for _ in range(4-len(platexy)):
        #     platexy = np.append(platexy,1)
        print(" ... M:\n", self.M)
        print(" ... xy:", platexy)
        motorxy = np.dot(self.M, platexy)
        motorxy = np.delete(motorxy, 2)
        motorxy = np.array(motorxy)[0]
        return motorxy

    def transform_motorxy_to_platexy(self, motorxy):
        """simply calculates platexy from current motorxy"""
        motorxy = np.asarray(motorxy)
        if len(motorxy) == 3:
            motorxy = np.insert(motorxy, 2, 0)
        print(" ... Minv:\n", self.Minv)
        print(" ... xy:", motorxy)
        platexy = np.dot(self.Minv, motorxy)
        platexy = np.delete(platexy, 2)
        platexy = np.array(platexy)[0]
        return platexy

    def transform_motorxyz_to_instrxyz(self, motorxyz):
        """simply calculatesinstrxyz from current motorxyz"""
        motorxyz = np.asarray(motorxyz)
        if len(motorxyz) == 3:
            # append 1 at end
            motorxyz = np.append(motorxyz, 1)
        print(" ... Minstrinv:\n", self.Minstrinv)
        print(" ... xyz:", motorxyz)
        instrxyz = np.dot(self.Minstrinv, motorxyz)
        return np.array(instrxyz)[0]

    def transform_instrxyz_to_motorxyz(self, instrxyz):
        """simply calculates motorxyz from current instrxyz"""
        instrxyz = np.asarray(instrxyz)
        if len(instrxyz) == 3:
            instrxyz = np.append(instrxyz, 1)
        print(" ... Minstr:\n", self.Minstr)
        print(" ... xyz:", instrxyz)

        motorxyz = np.dot(self.Minstr, instrxyz)
        return np.array(motorxyz)[0]

    def Rx(self):
        """returns rotation matrix around x-axis"""
        alphatmp = np.mod(self.alpha, 360)  # this actually takes care of neg. values
        # precalculate some common angles for better accuracy and speed
        if alphatmp == 0:  # or alphatmp == -0.0:
            return np.asmatrix(np.identity(4))
        elif alphatmp == 90:  # or alphatmp == -270:
            return np.matrix([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
        elif alphatmp == 180:  # or alphatmp == -180:
            return np.matrix([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])
        elif alphatmp == 270:  # or alphatmp == -90:
            return np.matrix([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]])
        else:
            return np.matrix(
                [
                    [1, 0, 0, 0],
                    [
                        0,
                        np.cos(np.pi / 180 * alphatmp),
                        -1.0 * np.sin(np.pi / 180 * alphatmp),
                        0,
                    ],
                    [
                        0,
                        np.sin(np.pi / 180 * alphatmp),
                        np.cos(np.pi / 180 * alphatmp),
                        0,
                    ],
                    [0, 0, 0, 1],
                ]
            )

    def Ry(self):
        """returns rotation matrix around y-axis"""
        betatmp = np.mod(self.beta, 360)  # this actually takes care of neg. values
        # precalculate some common angles for better accuracy and speed
        if betatmp == 0:  # or betatmp == -0.0:
            return np.asmatrix(np.identity(4))
        elif betatmp == 90:  # or betatmp == -270:
            return np.matrix([[0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 0, 1]])
        elif betatmp == 180:  # or betatmp == -180:
            return np.matrix([[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])
        elif betatmp == 270:  # or betatmp == -90:
            return np.matrix([[0, 0, -1, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]])
        else:
            return np.matrix(
                [
                    [
                        np.cos(np.pi / 180 * self.beta),
                        0,
                        np.sin(np.pi / 180 * self.beta),
                        0,
                    ],
                    [0, 1, 0, 0],
                    [
                        -1.0 * np.sin(np.pi / 180 * self.beta),
                        0,
                        np.cos(np.pi / 180 * self.beta),
                        0,
                    ],
                    [0, 0, 0, 1],
                ]
            )

    def Rz(self):
        """returns rotation matrix around z-axis"""
        gammatmp = np.mod(self.gamma, 360)  # this actually takes care of neg. values
        # precalculate some common angles for better accuracy and speed
        if gammatmp == 0:  # or gammatmp == -0.0:
            return np.asmatrix(np.identity(4))
        elif gammatmp == 90:  # or gammatmp == -270:
            return np.matrix([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        elif gammatmp == 180:  # or gammatmp == -180:
            return np.matrix([[-1, 0, 0, 0], [0, -1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        elif gammatmp == 270:  # or gammatmp == -90:
            return np.matrix([[0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        else:
            return np.matrix(
                [
                    [
                        np.cos(np.pi / 180 * gammatmp),
                        -1.0 * np.sin(np.pi / 180 * gammatmp),
                        0,
                        0,
                    ],
                    [
                        np.sin(np.pi / 180 * gammatmp),
                        np.cos(np.pi / 180 * gammatmp),
                        0,
                        0,
                    ],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1],
                ]
            )

    def Mx(self):
        """returns Mx part of Minstr"""
        Mx = np.asmatrix(np.identity(4))
        Mx[0, 0:4] = self.Minstrxyz[0, 0:4]
        print(" ... Mx", Mx)
        return Mx

    def My(self):
        """returns My part of Minstr"""
        My = np.asmatrix(np.identity(4))
        My[1, 0:4] = self.Minstrxyz[1, 0:4]
        print(" ... My", My)
        return My

    def Mz(self):
        """returns Mz part of Minstr"""
        Mz = np.asmatrix(np.identity(4))
        Mz[2, 0:4] = self.Minstrxyz[2, 0:4]
        print(" ... Mz", Mz)
        return Mz

    def Mplatewarp(self, platexy):
        """returns plate warp correction matrix (Z-correction. 
        Only valid for a single platexy coordinate"""
        return np.asmatrix(np.identity(4))  # TODO, just returns identity matrix for now

    def update_Msystem(self):
        """updates the transformation matrix for new plate calibration or
        when angles are changed.
        Follows stacking sequence from bottom to top (plate)"""

        print(" ... updatting M")

        if self.seq == None:
            print(" ... seq is empty, using default transformation")
            # default case, we simply have xy calibration
            self.M = np.dot(self.Minstrxyz, self.Mplate)
        else:
            self.Minstr = np.asmatrix(np.identity(4))
            # more complicated
            # check for some common sequences:
            Mcommon1 = (
                False  # to check against when common combinations are already found
            )
            axstr = ""
            for ax in self.seq.keys():
                axstr += ax
            # check for xyz or xy (with no z)
            # sequence does not matter so should define it like this in the config
            # if we want to use this
            if axstr.find("xy") == 0 and axstr.find("z") <= 2:
                print(" ... got xyz seq")
                self.Minstr = self.Minstrxyz
                Mcommon1 = True

            for ax in self.seq.keys():
                if ax == "x" and not Mcommon1:
                    print(" ... got x seq")
                    self.Minstr = np.dot(self.Minstr, self.Mx())
                elif ax == "y" and not Mcommon1:
                    print(" ... got y seq")
                    self.Minstr = np.dot(self.Minstr, self.My())
                elif ax == "z" and not Mcommon1:
                    print(" ... got z seq")
                    self.Minstr = np.dot(self.Minstr, self.Mz())
                elif ax == "Rx":
                    print(" ... got Rx seq")
                    self.Minstr = np.dot(self.Minstr, self.Rx())
                elif ax == "Ry":
                    print(" ... got Ry seq")
                    self.Minstr = np.dot(self.Minstr, self.Ry())
                elif ax == "Rz":
                    print(" ... got Rz seq")
                    self.Minstr = np.dot(self.Minstr, self.Rz())

            self.M = np.dot(self.Minstr, self.Mplate)

            # precalculate the inverse as we also need it a lot
            try:
                self.Minv = self.M.I
            except Exception:
                print(
                    "------------------------------ System Matrix singular ---------------------------"
                )
                # use the -1 to signal inverse later --> platexy will then be [x,y,-1]
                self.Minv = np.matrix(
                    [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, -1]]
                )

            try:
                self.Minstrinv = self.Minstr.I
            except Exception:
                print(
                    "------------------------------ Instrument Matrix singular ---------------------------"
                )
                # use the -1 to signal inverse later --> platexy will then be [x,y,-1]
                self.Minstrinv = np.matrix(
                    [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, -1]]
                )

            print(" ... new system matrix:")
            print(self.M)
            print(" ... new inverse system matrix:")
            print(self.Minv)

    def update_Mplatexy(self, Mxy):
        """updates the xy part of the plate calibration"""
        Mxy = np.matrix(Mxy)
        # assign the xy part
        self.Mplate[0:2, 0:2] = Mxy[0:2, 0:2]
        # assign the last row (offsets), notice the difference in col (3x3 vs 4x4)
        #        self.Mplate[0:2,3] = Mxy[0:2,2] # something does not work with this one is a 1x2 the other 2x1 for some reason
        self.Mplate[0, 3] = Mxy[0, 2]
        self.Mplate[1, 3] = Mxy[1, 2]
        # self.Mplate[3,0:4] should always be 0,0,0,1 and should never change

        # update the system matrix so we save calculation time later
        self.update_Msystem()

    def get_Mplatexy(self):
        """returns the xy part of the platecalibration"""
        self.Mplatexy = np.asmatrix(np.identity(3))
        self.Mplatexy[0:2, 0:2] = self.Mplate[0:2, 0:2]
        self.Mplatexy[0, 2] = self.Mplate[0, 3]
        self.Mplatexy[1, 2] = self.Mplate[1, 3]
        return self.Mplatexy

    def get_Mplate_Msystem(self, Mxy):
        """removes Minstr from Msystem to obtain Mplate for alignment"""
        Mxy = np.asarray(Mxy)
        Mglobal = np.asmatrix(np.identity(4))
        Mglobal[0:2, 0:2] = Mxy[0:2, 0:2]
        Mglobal[0, 3] = Mxy[0, 2]
        Mglobal[1, 3] = Mxy[1, 2]

        try:
            Minstrinv = self.Minstr.I
            Mtmp = np.dot(Minstrinv, Mglobal)
            self.Mplatexy = np.asmatrix(np.identity(3))
            self.Mplatexy[0:2, 0:2] = Mtmp[0:2, 0:2]
            self.Mplatexy[0, 2] = Mtmp[0, 3]
            self.Mplatexy[1, 2] = Mtmp[1, 3]

            return self.Mplatexy
        except Exception:
            print(
                "------------------------------ Instrument Matrix singular ---------------------------"
            )
            # use the -1 to signal inverse later --> platexy will then be [x,y,-1]
            self.Minv = np.matrix([[0, 0, 0], [0, 0, 0], [0, 0, -1]])

