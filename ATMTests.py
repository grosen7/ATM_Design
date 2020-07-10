from __future__ import annotations
import unittest, sys, typing
from Classes.ATM import ATM
from Classes.ControllerResponse import ControllerResponse
from Classes.SQLHelper import SQLHelper
from threading import Event

class ATMTests(unittest.TestCase):
    @classmethod
    def setUp(self):
        # create atm object with 3 second logout timer and point towards test db
        # this is mostly to be used with tests that don't require auth
        # create sql object that points towards test db
        self.atm = ATM(3, "Data/atmdb_test.db")
        self.sql = SQLHelper("Data/atmdb_test.db")

    # authorizes the first available account
    def AuthorizeAct(self, inactive: int = 3) -> ATM:
        atm = ATM(inactive, "Data/atmdb_test.db")
        data = self.sql.getSingleAccountCmd()
        accountId = data[0]
        pin = data[1]
        atm.controller("authorize {} {}".format(accountId, pin))
        return atm
    
    # tests authorizing a valid account
    def test_AuthorizeSuccess(self) -> None:
        print("Testing authorization of a valid account id and pin")
        # get first account id and pin in db
        data = self.sql.getSingleAccountCmd()
        accountId = data[0]
        pin = data[1]
        response = self.atm.controller("authorize {} {}".format(accountId, pin))
        # assert response is correct
        self.assertEqual("{} successfully authorized.".format(accountId), response.message)
        # assert account is authorized
        self.assertTrue(self.atm.account.isAuthorized)
        self.atm.controller
        self.atm.controller("end")

    # tests authorizing an invalid account id
    def test_AuthorizeBadAccountId(self) -> None:
        print("Testing authorization of an invalid account id")
        response = self.atm.controller("authorize 55555 1234")
        # assert response is correct
        self.assertEqual("Authorization failed.", response.message)
        # assert account is not authorized
        self.assertFalse(self.atm.account.isAuthorized)
        self.atm.controller("end")

    # tests authorizing a valid account with an invalid pin
    def test_AuthorizationBadPin(self) -> None:
        print("Testing authorization of a valid account id with an invalid pin")
        data = self.sql.getSingleAccountCmd()
        accountId = data[0]
        response = self.atm.controller("authorize {} 0000".format(accountId))
        # assert response is correct
        self.assertEqual("Authorization failed.", response.message)
        # assert account is not authorized
        self.assertFalse(self.atm.account.isAuthorized)
        self.atm.controller("end")

    # tests running through all commands, except logout & end 
    # that require authorizatio with no authorization
    def test_CommandsWithNoAuthorization(self) -> None:
        print("Testing running all commands (except logout & end) that require authorization with no authorization")
        responseLst = list()
        # run through commads and append response to list
        responseLst.append(self.atm.controller("balance").message)
        responseLst.append(self.atm.controller("history").message)
        responseLst.append(self.atm.controller("withdraw 20").message)
        responseLst.append(self.atm.controller("deposit 20").message)

        # validate that all responses were correct
        for response in responseLst:
            self.assertTrue(response == "Authorization required.")

        self.atm.controller("end")

    # Tests a valid withdrawal
    # Validates balances are correct at the end
    # and that response is correct
    def test_ValidWithdrawal(self) -> None:
        print("Testing a valid withdrawal of $20")
        atm = self.AuthorizeAct()
        # get current balances
        atmBal = atm.atmBalance
        actBal = atm.account.balance

        # validate atm has enough money, add 100 if it doesn't
        if atmBal < 20:
            atm.updateATMBalance(100)
            atmBal = 100
        
        # validate account has enough money 
        # add difference between 20 and account val + 1
        if actBal < 20:
            diff = 20 - atm.account.balance
            atm.account.updateAccountBalance(diff + 1)
            actBal += diff + 1

        # run withdraw command
        response = atm.controller("withdraw 20")
        # assert balances have been updated
        self.assertEqual(atmBal - 20, atm.atmBalance)
        self.assertEqual(actBal - 20, atm.account.balance)
        respMsg = "Amount dispensed: $20\nCurrent balance: {}".format(round(atm.account.balance,2))
        # validate response is correct
        self.assertEqual(response.message, respMsg)
        atm.controller("end")
    
    # tests a withdrawal that results in an overdraft fee
    # Validates balances are correct and response message is correct
    def test_OverdraftWithdrawal(self) -> None:
        print("Testing an overdraft withdrawal")
        atm = self.AuthorizeAct()
        actBal = atm.account.balance
        atmBal = atm.atmBalance

        # if account balance is less than 15 update
        if actBal < 15:
            diff = 15 - actBal
            atm.account.updateAccountBalance(diff)
            actBal += diff

        # if balance is greater than or equal to 20 update
        elif actBal >= 20:
            diff = actBal - 19
            atm.account.updateAccountBalance(diff * -1)
            actBal -= diff

        # if atm bal if under 20 update
        if atmBal < 20:
            atm.updateATMBalance(100)
            atmBal = 100
        
        response = atm.controller("withdraw 20")
        # assert balances have been updated and that overdraft fee was taken out of account
        self.assertEqual(atmBal - 20, atm.atmBalance)
        self.assertEqual(actBal - 25, atm.account.balance)
        message = ("Amount dispensed: $20\nYou have been charged an overdraft fee of "
                        "$5. Current balance: {}").format(round(atm.account.balance,2))
        # validate response is correct
        self.assertEqual(response.message, message)
        atm.controller("end")

    # Tests scenario where atm doesn't have enough to complete full withdrawal
    # Validates balances are correct and response message is correct
    def test_InvalidAtmAmtWithdrawl(self) -> None:
        print("Testing a scenario where the atm doesn't have enough to dispense full amount")
        atm = self.AuthorizeAct()
        atmBal = atm.atmBalance
        actBal = atm.account.balance

        # adjust atm balance if necessary
        if atmBal != 15:
            atm.updateATMBalance(15)
            atmBal = 15
        
        # adjust act bal if necessary
        if actBal < 20:
            diff = 20 - actBal
            atm.account.updateAccountBalance(diff)
            actBal += diff

        response = atm.controller("withdraw 20")
        self.assertEqual(0, atm.atmBalance)
        self.assertEqual(actBal - 15, atm.account.balance)
        message = "Unable to dispense full amount requested at this time. Amount dispensed: $15\nCurrent balance: {}".format(round(atm.account.balance,2))
        self.assertEqual(message, response.message)
        atm.controller("end")

    # tests scenario where atm has no money to dispense
    # validates atm balance and response
    def test_AtmEmptyWithdrawal(self) -> None:
        print("Testing scenario where atm has no money to dispense")
        atm = self.AuthorizeAct()
        atmBal = atm.atmBalance
        actBal = atm.account.balance

        # adjust atm balance if necessary
        if atmBal != 0:
            atm.updateATMBalance(0)
            atmBal = 0

        if actBal < 0:
            atm.account.updateAccountBalance(abs(actBal) + 1)
            actBal = abs(actBal) + 1

        response = atm.controller("withdraw 20")
        self.assertEqual(0, atm.atmBalance)
        message = "Unable to process your withdrawal at this time."
        self.assertEqual(response.message, message)
        atm.controller("end")

    # tests scenario where account is overdrawn
    def test_AccountOverdrawnWithdrawal(self) -> None:
        print("Testing scenario where account is overdrawn")
        atm = self.AuthorizeAct()
        actBal = atm.account.balance
        
        if actBal >= 0:
            diff = -1 - actBal
            atm.account.updateAccountBalance(diff)
            actBal += diff

        response = atm.controller("withdraw 20")
        self.assertEqual(actBal, atm.account.balance)
        message = "Your account is overdrawn! You may not make withdrawals at this time."
        self.assertEqual(message, response.message)
        atm.controller("end")

    # tests scenario where negative withdrawal amount given 
    def test_NegativeWitdrawal(self) -> None:
        print("Testing scenarion where negative withdrawal amount is given")
        atm = self.AuthorizeAct()
        response = atm.controller("withdraw -20")
        message = "Withdrawal amount must be greater than 0 and in increments of 20."
        self.assertEqual(response.message, message)
        atm.controller("end")

    # tests scenario where an non multiple of 20 withdrawal amount given 
    def test_NotMultOf20Witdrawal(self) -> None:
        print("Testing scenarion where an amount that isn't a multiple of 20 is provided for withdrawal")
        atm = self.AuthorizeAct()
        response = atm.controller("withdraw 15")
        message = "Withdrawal amount must be greater than 0 and in increments of 20."
        self.assertEqual(response.message, message)
        atm.controller("end")

    # tests a valid deposit of $20
    def test_ValidDeposit(self) -> None:
        print("Testing valid deposit of $20")
        atm = self.AuthorizeAct()
        atmBal = atm.atmBalance
        actBal = atm.account.balance
        response = atm.controller("deposit 20")
        self.assertEqual(atmBal + 20, atm.atmBalance)
        self.assertEqual(actBal + 20, atm.account.balance)
        message = "Current balance: {}".format(atm.account.balance)
        self.assertEqual(message, response.message)
        atm.controller("end")

    # tests an invalid deposit of 0
    def test_ZeroDeposit(self) -> None:
        print("Testing scenario where $0 is deposited")
        atm = self.AuthorizeAct()
        response = atm.controller("deposit 0")
        message = "Deposit amount must be greater than 0."
        self.assertEqual(response.message, message)
        atm.controller("end")

    # tests an invalid deposit of -5
    def test_NegativeDeposit(self) -> None:
        print("Testing scenario where $-5 is deposited")
        atm = self.AuthorizeAct()
        response = atm.controller("deposit -5")
        message = "Deposit amount must be greater than 0."
        self.assertEqual(response.message, message)
        atm.controller("end")

    # tests balance command
    def test_Balance(self) -> None:
        print("Testing balance command")
        atm = self.AuthorizeAct()
        response = atm.controller("balance")
        message = "Current balance: {}".format(atm.account.balance)
        self.assertEqual(message, response.message)
        atm.controller("end")

    # tests balance by depositing and then checking history is not null
    def test_History(self) -> None:
        print("Testing history command")
        atm = self.AuthorizeAct()
        atm.controller("deposit 20")
        response = atm.controller("history")
        self.assertIsNotNone(response.message)
        atm.controller("end")

    # tests scenario where account has no history
    # validates response is correct
    def test_NoHistory(self) -> None:
        print("Testing scenario where there is no account history")
        atm = self.AuthorizeAct()
        self.sql.clearAccountHistoryCmd(atm.account.accountId)
        response = atm.controller("history")
        self.assertEqual(response.message, "No history found")
        atm.controller("end")

    # tests logging out of valid account
    # validate authorized flag is false
    # and response message is correct
    def test_ValidLogout(self) -> None:
        print("Testing normal logout")
        atm = self.AuthorizeAct()
        accountId = atm.account.accountId
        response = atm.controller("logout")
        message = "Account {} logged out.".format(accountId)
        self.assertFalse(atm.account.isAuthorized)
        self.assertEqual(message, response.message)
        atm.controller("end")

    # tests logging out of account when one isn't logged in
    # validate authorized flag is false
    # and response message is correct
    def test_InvalidLogout(self) -> None:
        print("Testing logging out when no account is logged in")
        atm = ATM()
        response = atm.controller("logout")
        message = "No account is currently authorized."
        self.assertEqual(message, response.message)
        self.assertFalse(atm.account.isAuthorized)
        atm.controller("end")

    # tests that user is logged out after 4 seconds
    # when inactive logout is set to 3 seconds
    def test_InactiveLogout(self) -> None:
        print("Testing scenario where user is inactive and is logged out")
        atm = self.AuthorizeAct()
        sleep = Event()
        sleep.wait(4)
        self.assertFalse(atm.account.isAuthorized)

    # tests inputs that should trigger error when given while user logged in
    # asserts error flag is raised and 
    def test_BadInputLoggedIn(self) -> None:
        print("Testing a few scenarios where user is logged in and gives bad input")
        atm = self.AuthorizeAct()
        badInput = ["deposit 1 2 3 4", "withdraw 5634 095376", "26235742", "2438g346"]
        
        for bad in badInput:
            response = atm.controller(bad)
            self.assertEqual("Invalid command detected.", response.message)
            self.assertTrue(response.error)
        
        atm.controller("end")

    # tests inputs that should trigger error when given while user not logged in
    # asserts error flag is raised and 
    def test_BadInputNotLoggedIn(self) -> None:
        print("Testing a few scenarios where user is not logged in and gives bad input")
        atm = ATM(3,"Data/atmdb_test.db")
        badInput = ["deposit 1 2 3 4", "withdraw 5634 095376", "26235742", "2438g346"]
        
        for bad in badInput:
            response = atm.controller(bad)
            self.assertEqual("Invalid command detected.", response.message)
            self.assertTrue(response.error)
        
        atm.controller("end")

if __name__ == "__main__":
    unittest.main()