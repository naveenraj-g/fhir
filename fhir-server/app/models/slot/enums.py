from enum import Enum


class SlotStatus(str, Enum):
    BUSY = "busy"
    FREE = "free"
    BUSY_UNAVAILABLE = "busy-unavailable"
    BUSY_TENTATIVE = "busy-tentative"
    ENTERED_IN_ERROR = "entered-in-error"


class SlotScheduleReferenceType(str, Enum):
    SCHEDULE = "Schedule"
