from typing import Callable


class RiposteException(Exception):
    pass


class StopRiposteException(Exception):
    pass


class CommandError(RiposteException):
    pass


class GuideError(RiposteException):
    def __init__(self, value: str, guide: Callable):
        self.value = value
        self.guide = guide

    def __str__(self):
        return (
            f"GuideError: Can't apply "
            f"{self.guide.__name__} guide "
            f"to value {self.value}"
        )
