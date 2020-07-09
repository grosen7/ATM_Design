from __future__ import annotations
import typing

class ControllerResponse:
    def __init__(self) -> ControllerResponse:
        self.message = None
        self.error = False
        self.end = False

    # update controller response message and error flag
    def addResponseMsg(self, message: str) -> None:
        self.message = message

    # updates error flag
    def updateErrorFlag(self, error: bool) -> None:
        self.error = error

    # sets controller end flag
    def setEndFlag(self) -> None:
        self.end = True