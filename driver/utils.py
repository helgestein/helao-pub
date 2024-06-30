import numpy as np
from abc import ABC
from enum import Enum
from datetime import datetime
from dataclasses import dataclass


class MemoryType(Enum):
    """Enumeration for different types of memory."""

    ABSOLUTE = 0
    RELATIVE = 1
    END_EFFECTOR = 2


class MotionType(Enum):
    """Enumeration for different types of motion."""

    JOINT = 0
    LINEAR = 1
    GRIPPER = 2
    SUCTION_CUP = 3


@dataclass
class MemoryEntry:
    """Represents an entry in the memory.

    Attributes:
        type (MemoryType): The type of memory entry.
        value (np.ndarray): The value associated with the memory entry.
            [x, y, z, r] for ABSOLUTE, [j1, j2, j3, j4] for RELATIVE, [index, value] for END_EFFECTOR.
        motion_type (MotionType): The motion type of the memory entry.
        valid (bool): Indicates whether the memory entry is valid or not.
    """

    type: MemoryType
    motion_type: MotionType
    value: np.ndarray
    valid: bool = True

    def serialize(self) -> dict:
        """Serializes the MemoryEntry object into a dictionary.

        Returns:
            dict: A dictionary representation of the MemoryEntry object.
        """
        return {
            "Type": self.type.name,
            "Motion Type": self.motion_type.name,
            "Value": [
                float(el)
                if self.type != MemoryType.END_EFFECTOR
                else [float(iel) for iel in el]
                for el in list(self.value)
            ],
            "Valid": self.valid,
        }

    @staticmethod
    def from_dict(entry: dict) -> "MemoryEntry":
        """Creates a MemoryEntry object from a dictionary.

        Args:
            entry (dict): A dictionary containing the memory entry information.

        Returns:
            MemoryEntry: A MemoryEntry object created from the dictionary.
        """
        return MemoryEntry(
            MemoryType[entry["Type"]],
            MotionType[entry["Motion Type"]],
            np.array(entry["Value"]),
            entry["Valid"],
        )


@dataclass
class FeedEntry:
    """Represents an entry in the feed.

    Attributes:
        timestamp (datetime): The timestamp of the feed entry.
        message (str): The message of the feed entry.
        source (str): The source of the feed entry.
    """

    timestamp: datetime
    message: str
    source: str

    def serialize(self) -> dict:
        """Serializes the FeedEntry object into a dictionary.

        Returns:
            dict: A dictionary representation of the FeedEntry object.
        """
        return {
            "Timestamp": self.timestamp.strftime("%H:%M:%ST%d.%m.%Y"),
            "Message": self.message,
            "Source": self.source,
        }

    @staticmethod
    def from_dict(entry: dict) -> "FeedEntry":
        """Creates a FeedEntry object from a dictionary.

        Args:
            entry (dict): A dictionary containing the feed entry information.

        Returns:
            FeedEntry: A FeedEntry object created from the dictionary.
        """
        return FeedEntry(
            datetime.strptime(entry["Timestamp"], "%H:%M:%ST%d.%m.%Y"),
            entry["Message"],
            entry["Source"],
        )


@dataclass
class Keymap:
    """Represents a playstation controller keymap."""

    cross_pressed: callable
    square_pressed: callable
    triangle_pressed: callable
    circle_pressed: callable
    r1_changed: callable
    l1_changed: callable
    r2_changed: callable
    l2_changed: callable
    left_joystick_changed: callable
    right_joystick_changed: callable
    dpad_up: callable
    dpad_down: callable
    dpad_left: callable
    dpad_right: callable


class EndEffectorType(Enum):
    """Enumeration for different types of end effectors."""

    NO_END_EFFECTOR = 0
    SUCTION_CUP = 1
    GRIPPER = 2


@dataclass
class EndEffectorPins(ABC):
    """Base class representing the pins of the end effector."""

    pass


@dataclass
class AirPumpPins(EndEffectorPins):
    """Represents the pins of the air pump."""

    power: int
    direction: int


# Map end effector types to their respective pin mappings
pin_mapping = {
    EndEffectorType.NO_END_EFFECTOR: None,
    EndEffectorType.GRIPPER: AirPumpPins,
    EndEffectorType.SUCTION_CUP: AirPumpPins,
}
