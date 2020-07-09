from __future__ import annotations
from SQLHelper import SQLHelper
import typing

class Account:
    def __init__(self) -> Account:
        self.accountId = None
        self.balance = None
        self.isAuthorized = False
        self.sql = SQLHelper()

    # updates account details
    def addAccountDetails(self, accountId: int, balance: int, isAuthorized: bool = True) -> None:
        self.accountId = accountId
        self.balance = balance
        self.isAuthorized = isAuthorized

    # update account balance in db and in memory
    # if withdrawal, change amount to negative
    # also update account history in db
    def updateAccountBalance(self, amount: int) -> None:
        newBalance = self.balance + amount
        self.sql.updateBalanceCmd(self.accountId, amount, newBalance)
        self.balance = newBalance
        # update account history
        self.sql.updateHistoryCmd(self.accountId, amount, newBalance)
