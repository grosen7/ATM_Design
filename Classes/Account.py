import typing
from __future__ import annotations

class Account:
    def __init__(self) -> None:
        self.accountId = None
        self.balance = None
        self.isAuthorized = False

    # given the account id and pin, verify account in db
    # if account exists, set object parameters and return object
    # if account doesn't exist return default account
    def authorizeAccount(self, accountId: int, pin: int) -> Account:
        pass