from __future__ import annotations
import typing

class ControllerResponse:
    def __init__(self) -> ControllerResponse:
        self.message = None
        self.error = False
        self.end = False

    # update controller response message and error flag
    def updateResponse(self, message: str, error: bool = False) -> None:
        self.message = message
        self.error = error

    # sets controller end flag
    def setEndFlag(self) -> None:
        self.end = True