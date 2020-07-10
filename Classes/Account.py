from __future__ import annotations
from Classes.SQLHelper import SQLHelper
import typing

class Account:
    def __init__(self, db: str = "Data/atmdb.db") -> Account:
        self.accountId = None
        self.balance = None
        self.isAuthorized = False
        self.sql = SQLHelper(db)

    # updates account details
    def addAccountDetails(self, accountId: int, balance: int, isAuthorized: bool = True) -> None:
        self.accountId = accountId
        self.balance = balance
        self.isAuthorized = isAuthorized

    # update account balance in db and in memory
    # if withdrawal, change amount to negative
    # amount is added to current amount (doesn't just set the amount)
    # also update account history in db
    def updateAccountBalance(self, amount: int) -> None:
        newBalance = self.balance + amount
        self.sql.updateBalanceCmd(self.accountId, amount, newBalance)
        self.balance = newBalance
        # update account history
        self.sql.updateHistoryCmd(self.accountId, round(amount,2), round(newBalance,2))
