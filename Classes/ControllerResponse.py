import typing
from __future__ import annotations

class ControllerResponse:
    def __init__(self, message: str, error: bool = False) -> None:
        self.message = None
        self.error = error
        self.end = False

    def setEndFlag(self) -> None:
        self.end = True