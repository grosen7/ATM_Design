from __future__ import annotations
from typing import List
from Classes.ControllerResponse import ControllerResponse
from Classes.Account import Account
from Classes.SQLHelper import SQLHelper
from threading import Timer, Event

class ATM:
    # constructor, inactive logout time by default is 2 minutes
    # db by default is atmdb
    def __init__(self, inactiveTime: int = 120, db: str = "Data/atmdb.db") -> ATM:
        # commands that require and account to be authorized before running
        self.preauthCmds = ["withdraw", "deposit", "balance", "history"]
        self.sql = SQLHelper(db)
        self.atmBalance = self.sql.getATMBalanceCmd()
        self.inactiveTime = inactiveTime
        # timer that after inactiveTime runs inactiveLogout method
        self.timer = Timer(self.inactiveTime, self.inactiveLogout)
        self.activeTimer = False
        self.db = db
        self.account = Account(self.db)

    # updates atm balance in memory and in db
    # to specified amount
    def updateATMBalance(self, amount: int):
        self.sql.updateATMBalance(amount)
        self.atmBalance = amount

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
        self.updateATMBalance(newAtmBal)
        self.account.updateAccountBalance(actAmt)

    # uses accountSelectCmd from sqlhelper to get account using account id
    # checks that the provided pin matches the pin on file
    # if pin matches account is authorized, otherwise account is not authorized
    def authorize(self, accountId: int, pin: int) -> ControllerResponse:
        response = ControllerResponse()

        # check if an account is already authorized, if one is then return
        if self.account.isAuthorized:
            message = "An account is already authorized. Logout before authorizing another account."
            response.addResponseMsg(message)
            return response

        # search for account data
        actData = self.sql.accountSelectCmd(accountId)

        # if no account exists with the provided account id then return
        # failed authorization
        if not actData:
            message = "Authorization failed."
            response.addResponseMsg(message)
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

        response.addResponseMsg(message)
        return response

    # validate that account is authorized the withdraw amount
    # validate that atm and account have enough money
    def withdraw(self, amount: int) -> ControllerResponse:
        response = ControllerResponse()

        # if the amount is not greater than 0 and not an increment of 20 update response message
        # exit immediately
        if amount <= 0 or amount % 20 != 0:
            message = "Withdrawal amount must be greater than 0 and in increments of 20."
            response.addResponseMsg(message)
            return response
        # if the account is overdrawn update the response message
        # and exit immediately
        elif self.account.balance < 0:
            message = "Your account is overdrawn! You may not make withdrawals at this time."
            response.addResponseMsg(message)
            return response
        # if the atm has no money update response message and return
        elif self.atmBalance == 0:
            message = "Unable to process your withdrawal at this time."
            response.addResponseMsg(message)
            return response
        
        message = ""

        # if there isn't enough in the atm, update amount requested to atm balance
        # prepend unable to dispense full amount message to return message
        if amount > self.atmBalance:
            message = "Unable to dispense full amount requested at this time. "
            amount = self.atmBalance

        # if there is enough in the account
        # update account and atm balance
        if amount <= self.account.balance:
            self.updateBalances(amount, True)
            message += "Amount dispensed: ${}\nCurrent balance: {}".format(amount, round(self.account.balance,2))
        # if there is money in the account but not enough
        # add an extra 5 to withdrawal amount
        # update account and atm balance
        elif 0 < self.account.balance < amount:
            self.updateBalances(amount, True, True)
            message += ("Amount dispensed: ${}\nYou have been charged an overdraft fee of "
                        "$5. Current balance: {}").format(amount, round(self.account.balance,2))

        # update response message
        response.addResponseMsg(message)
        return response


    # deposits provided amount into bank account
    def deposit(self, amount: int) -> ControllerResponse:
        if amount > 0:
            self.updateBalances(amount, False)
            message = "Current balance: {}".format(round(self.account.balance,2))
        else:
            message = "Deposit amount must be greater than 0."
        
        # update response and return
        response = ControllerResponse()
        response.addResponseMsg(message)
        return response

    # Finds balance of authorized account
    def getBalance(self) -> ControllerResponse:
        response = ControllerResponse()
        response.addResponseMsg("Current balance: {}".format(round(self.account.balance,2)))
        return response

    # get history from db then format into string
    def getHistory(self) -> ControllerResponse:
        message = ""
        sqlData = self.sql.getHistoryCmd(self.account.accountId)

        # if no history found update message
        # otherwise grab history
        if len(sqlData) == 0:
            message = "No history found"
        else:
            for row in sqlData:
                message += "{} {} {} {}\n".format(row[0], row[1], round(row[2],2), round(row[3],2))
        
        response = ControllerResponse()
        response.addResponseMsg(message)
        return response


    # if an account is logged in then log out and update response message
    # if no account is logged in then just update response message
    def logout(self) -> ControllerResponse:
        if self.account.isAuthorized:
            message = "Account {} logged out.".format(self.account.accountId)
            self.account = Account(self.db)
        else:
            message = "No account is currently authorized."
        
        response = ControllerResponse()
        response.addResponseMsg(message)
        return response

    # method that is called by timer when time is up
    # logs out user and sets active timer flag to false
    def inactiveLogout(self) -> None:
        self.account = Account(self.db)
        self.activeTimer = False
        self.timer = Timer(self.inactiveTime, self.inactiveLogout)

    # starts the inactive timer if one isn't running and account is authorized
    def startInactiveTimer(self) -> None:
        if self.account.isAuthorized and not self.activeTimer:
            self.timer.start()
            self.activeTimer = True

    # stops the inactive timer if one is running
    def stopInactiveTimer(self) -> None:
        # if a timer is running, cancel timer, reset flag
        # and create new timer object
        if self.activeTimer:
            self.timer.cancel()
            self.activeTimer = False
            self.timer = Timer(self.inactiveTime, self.inactiveLogout)

    # end program
    def endProgram(self) -> ControllerResponse:
        response = ControllerResponse()
        response.setEndFlag()
        response.addResponseMsg("Goodbye!")
        return response

    # logs error to db
    def logError(self, error: Exception) -> None:
        errorMsg = str(error)
        # escape single quotes
        errorMsg = errorMsg.replace("'","''")
        self.sql.logErrorCmd(self.account.accountId, errorMsg)

    # validates user input
    # checks length and data types
    def validateInput(self, usrInput: str) -> List[object]:
        # strip and split user input
        cmdParts = usrInput.strip().split()

        # no command should have over 3 arguments, raise exception
        if len(cmdParts) > 3:
            raise Exception("Too many arguments detected in command: {}".format(usrInput))

        firstPart = cmdParts[0].lower()
        # commands that should only have 2 parts
        twoPartCmds = ["withdraw", "deposit"]
        onePartCmds = ["balance", "history", "logout", "end"]

        # if the command has three parts it should be authorize
        if len(cmdParts) == 3 and firstPart != "authorize":
            raise Exception("Too many arguments detected in command: {}".format(usrInput))
        # if it has two pasts it should just be withdraw or deposit
        elif len(cmdParts) == 2 and firstPart not in twoPartCmds:
             raise Exception("Too many arguments detected in command: {}".format(usrInput))
        # if in one part commands, should only be one command
        elif firstPart in onePartCmds and len(cmdParts) != 1:
             raise Exception("Too many arguments detected in command: {}".format(usrInput))

        validCmds = list()
        validCmds.append(firstPart)

        # loop through all provided commands 
        # first command should be string
        # all other parts should be ints
        for i in range(1, len(cmdParts)):
            argVal = int(cmdParts[i].strip())
            validCmds.append(argVal)
        
        return validCmds
        

    # controls logic flow of class
    # routes to different methods based on valid user input
    # starts and stops inactivity timer
    def controller(self, userInput: str) -> ControllerResponse:
        self.stopInactiveTimer()

        # minimal error handling for simplicity
        # one try block, if error occurs log and return generic response
        try:
            # raise exception
            if len(userInput.strip()) == 0:
                raise Exception("No input detected.")
            
            # parse commands if valid, exception raised if not valid
            cmds = self.validateInput(userInput)
            initArg = cmds[0]

            # if the command is in the list of commands that need authorization
            # validate that the account is authorized
            if initArg in self.preauthCmds:
                # if the account is authorized then route and run command
                if self.account.isAuthorized:
                    if initArg == "withdraw":
                        response = self.withdraw(cmds[1])
                    elif initArg == "deposit":
                        response = self.deposit(cmds[1])
                    elif initArg == "balance":
                        response = self.getBalance()
                    elif initArg == "history":
                        response = self.getHistory()
                # if the account isn't authorized, update response
                else:
                    response = ControllerResponse()
                    response.addResponseMsg("Authorization required.")
            # if command doesn't need preauth then run them
            elif initArg == "authorize":
                response = self.authorize(cmds[1], cmds[2])
            elif initArg == "logout":
                response = self.logout()
            elif initArg == "end":
                response = self.endProgram()
            # otherwise command isn't recognized, throw error
            else:
                raise Exception("Invalid command detected: {}".format(userInput))

        # if there is an error, log to db and update controller message
        except Exception as e:
            self.logError(e)
            message = "Invalid command detected."
            response = ControllerResponse()
            response.addResponseMsg(message)
            response.updateErrorFlag(True)
        
        # start inactive timer unless if program is ending
        if not response.end:
            self.startInactiveTimer()

        return response