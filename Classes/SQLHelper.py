import typing
from Classes.Account import Account

class SQLHelper:
    def __init__(self) -> None:
        pass

    def insert(self, command: str) -> None:
        pass

    def update(self, command: str) -> None:
        pass

    def select(self, command: str) -> None:
        pass

    # verify that pin is correct for given accountid
    # returns balance and accountid
    def authorizationCmd(self, accountId: int, pin: int) -> None:
        pass
    
    # withdraw certain amount from given account
    # returns remaining balance maybe?
    def witdrawCmd(self, account: Account, amount: int) -> None:
        pass

    # returns transaction history for account
    def getHistoryCmd(self, account: Account) -> None:
        pass

    # updates account history
    def updateHistoryCmd(self, accountId, message: str) -> None:
        pass