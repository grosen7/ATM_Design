from __future__ import annotations
import typing, math
from ControllerResponse import ControllerResponse
from Account import Account
from SQLHelper import SQLHelper
from threading import Timer

class ATM:
    # constructor, inactive logout time by default is 2 minutes
    def __init__(self, inactiveLogout : int = 120) -> ATM:
        self.account = Account()
        # commands that require and account to be authorized before running
        self.preauthCmds = ["withdraw", "deposit", "balance", "history", "logout"]
        self.sql = SQLHelper()
        self.atmBalance = self.sql.getATMBalanceCmd()
        # timer that after inactiveLogout runs inactiveLogout method
        self.timer = Timer(inactiveLogout, self.inactiveLogout)
        self.activeTimer = False

    # updates atm and account balances
    def updateBalances(self, amount: int, withdrawal: bool, overdraft: bool = False) -> None:
        actAmt = amount
        atmAmt = amount

        # if this transaction overdrafts the account subtract an additional 5
        if overdraft:
            actAmt += 5
        
        # if the is is a withdrawal turn amount negative
        if withdrawal:
            actAmt *= -1
            atmAmt *= -1
        
        # run methods to update atm and account balances
        newAtmBal = self.atmBalance + atmAmt
        self.sql.updateATMBalance(newAtmBal)
        self.account.updateAccountBalance(atmAmt)

    # uses accountSelectCmd from sqlhelper to get account using account id
    # checks that the provided pin matches the pin on file
    # if pin matches account is authorized, otherwise account is not authorized
    def authorize(self, accountId: int, pin: int) -> ControllerResponse:
        response = ControllerResponse()

        # check if an account is already authorized, if one is then return
        if self.account.isAuthorized:
            message = "An account is already authorized. Logout before authorizing another account."
            response.updateResponse(message)
            return response

        # search for account data
        actData = self.sql.accountSelectCmd(accountId)

        # if no account exists with the provided account id then return
        # failed authorization
        if len(actData) == 0:
            message = "Authorization failed."
            response.updateResponse(message)
            return response

        # get pin number
        actPin = actData[2]

        # if the pin on file matches the provided pin then authorize account
        if actPin == pin:
            balance = actData[3]
            self.account.addAccountDetails(accountId, balance, True)
            message = "{} successfully authorized.".format(accountId)
        # otherwise fail authorization
        else:
            message = "Authorization failed."

        response.updateResponse(message)
        return response

    # validate that account is authorized the withdraw amount
    # validate that atm and account have enough money
    def withdraw(self, amount: int) -> ControllerResponse:
        response = ControllerResponse()
        message = ""

        # if the atm has no money update response message and return
        if self.atmBalance == 0:
            message = "Unable to process your withdrawal at this time."
            response.updateResponse(message)
            return response
        # if the amount is not greater than 0 and not an increment of 20 update response message
        elif amount <= 0 or amount % 20 != 0:
            message = "Withdrawawl amount must be greater than 0 and in increments of 20."
            response.updateResponse(message)
            return response

        # if there isn't enough in the atm, update amount requested to atm balance
        # prepend unable to dispense full amount message to return message
        if amount > self.atmBalance:
            message = "Unable to dispense full amount requested at this time. "
            amount = self.atmBalance

        # if there is enough in the atm
        if amount <= self.atmBalance:
            # if there is enough in the account
            # update account and atm balance
            if amount <= self.account.balance:
                self.updateBalances(amount, True)
                message += "Amount dispensed: ${}\n Current balance: {}".format(amount, self.account.balance)
            # if there is money in the account but not enough
            # add an extra 5 to withdrawal amount
            # update account and atm balance
            elif 0 < self.account.balance < amount:
                self.updateBalances(amount, True, True)
                message += """Amount dispensed: ${}\n You have been charged an overdraft fee of 
                            $5 Current balance: {}""".format(amount, self.account.balance)
            # if the account is overdrawn update the response message
            elif self.account.balance <= 0:
                message += "Your account is overdrawn! You may not make withdrawals at this time."
            
        # update response message
        response.updateResponse(message)
        return response


    # deposits provided amount into bank account
    def deposit(self, amount: int) -> ControllerResponse:
        if amount > 0:
            self.updateBalances(amount, False)
            message = "Current balance: {}".format(self.account.balance)
        else:
            message = "Deposit amount must be greater than 0."
        
        # update response and return
        response = ControllerResponse()
        response.updateResponse(message)
        return response

    # Finds balance of authorized account
    def getBalance(self) -> ControllerResponse:
        response = ControllerResponse()
        response.updateResponse("Current balance: {}".format(self.account.balance))
        return response

    # get history from db then format into string
    def getHistory(self) -> ControllerResponse:
        message = ""
        sqlData = self.sql.getHistoryCmd(self.account.accountId)

        for row in sqlData:
            message += "{} {} {} {}\n".format(row[0], row[1], row[2], row[3])
        
        response = ControllerResponse()
        response.updateResponse(message)
        return response


    # if an account is logged in then log out and update response message
    # if no account is logged in then just update response message
    def logout(self) -> ControllerResponse:
        if self.account.isAuthorized:
            message = "Account {} logged out.".format(self.account.accountId)
            self.account = Account()
        else:
            message = "No account is currently authorized."
        
        response = ControllerResponse()
        response.updateResponse(message)
        return response

    # method that is called by timer when time is up
    # logs out user if logged in
    def inactiveLogout(self) -> None:
        if self.account.isAuthorized:
            self.account = Account()

    # starts the inactive timer if one isn't running and account is authorized
    def startInactiveTimer(self) -> None:
        if self.account.isAuthorized and not self.activeTimer:
            self.timer.start()
            self.activeTimer = True

    # stops the inactive timer if one is running
    def stopInactiveTimer(self) -> None:
        if self.activeTimer:
            self.timer.cancel()
            self.activeTimer = False


    # end program
    def endProgram(self) -> ControllerResponse:
        response = ControllerResponse()
        response.updateResponse("end")
        response.setEndFlag()
        return response

    # controls logic flow of class
    # routes to different methods based on valid user input
    # starts and stops inactivity timer
    def controller(self, userInput: str) -> ControllerResponse:
        self.stopInactiveTimer()
        response = ControllerResponse()

        try:
            # TODO: first action should be to stop threaded timer if running
            # return invalid command message if no input
            if len(userInput.strip()) == 0:
                return
            
            # strip and split command
            # then get first part of command, strip and lower
            cmdParts = userInput.strip().split()
            firstPart = cmdParts[0].strip().lower()
        
            if firstPart in self.preauthCmds:
                if self.account.isAuthorized:
                    # run command
                    pass
                else:
                    message = "Authorization required."
            
            response.updateResponse(message)
        except Exception as e:
            # TODO: error handling
            pass
        
        # TODO: at the end of this method start the inactive timer
        self.startInactiveTimer()
        return response

    # uses threaded timer to keep track of time
    # logout account if timer reaches 2 minutes
    def inactivityLogout(self):
        pass
    
if __name__ == "__main__":
    obj = ATM()
    obj.authorize(2859459814, 7386)
    test = obj.getHistory()
    print("ere")