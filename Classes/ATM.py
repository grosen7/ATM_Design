import typing
from Classes.ControllerResponse import ControllerResponse
from Classes.Account import Account

class ATM:
    def __init__(self, atmBalance: int = 10000) -> None:
        self.account = Account()
        self.atmBalance = atmBalance
    
    # updates atm balance, if deposit is false transaction is a withdrawal
    # otherwise transaction is a deposit
    def updateATMBalance(self, amount: int, deposit: bool = False) -> None:
        if not deposit:
            self.atmBalance += deposit
        else:
            self.atmBalance -= deposit

    #uses authorizeAccount method from account class to authorize 
    def authorize(self, accountId: int, pin: int) -> ControllerResponse:
        pass
    
    # validate that account is authorized then use sql class to update balance
    def withdraw(self, amount: int) -> ControllerResponse:
        pass

    # validate that account is authorized then use sql class to update balance
    def deposit(self, amount: int) -> ControllerResponse:
        pass

    # balance should be save in memory, return the balance
    def getBalance(self) -> ControllerResponse:
        pass

    # validate that account is authorized then get account history with sql class
    def getHistory(self) -> ControllerResponse:
        pass

    # validate that an account is logged in then logout by setting account obj to default
    def logout(self) -> ControllerResponse:
        pass
    
    # end program
    def endProgram(self) -> ControllerResponse:
        pass

    # call method based on user input, if user input is not recognized exit
    # if an account is logged in, start threaded timer
    def controller(self, userInput: str) -> ControllerResponse:
        pass

    # uses threaded timer to 
    # need to figure out if we logout or end program then restart here
    def inactivityLogout(self):
        pass
    
