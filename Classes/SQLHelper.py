from __future__ import annotations
from typing import List, Tuple
import sqlite3
from datetime import datetime

class SQLHelper:
    def __init__(self, dbFile: str) -> None:
        self.cursor = self.connect(dbFile)
    
    # connect to provided data base, return db cursor
    # to execute commands
    def connect(self, dbFile: str) -> cursor:
        conn = sqlite3.connect(dbFile, isolation_level = None)
        cursor = conn.cursor()
        return cursor

    # returns account data bas
    def accountSelectCmd(self, accountId: int) -> List[Tuple[object]]:
        self.cursor.execute("SELECT * FROM accounts WHERE account_id = {};".format(accountId))
        data = self.cursor.fetchone()
        return data
    
    # update account balance
    # add transaction to history table
    def updateBalanceCmd(self, accountId: int, amount: int, updatedAmount: int) -> None:
        self.cursor.execute("UPDATE accounts SET balance = {} WHERE account_id = {};".format(updatedAmount, accountId))
        self.updateHistoryCmd(accountId, amount, updatedAmount)

    # returns transaction history for account
    def getHistoryCmd(self, accountId: int) -> List[Tuple[object]]:
        self.cursor.execute("""SELECT date, time, amount, new_balance FROM history WHERE account_id = {} 
                                ORDER BY date, time desc;""".format(accountId))
        data = self.cursor.fetchall()
        return data

    # inserts row into history table with necessary transaction data
    def updateHistoryCmd(self, accountId: int, amount: int, updatedAmount: int) -> None:
        date = datetime.today().strftime("%Y-%m-%d")
        time = datetime.now().strftime("%H:%M:%S")
        self.cursor.execute(
            """INSERT INTO history(account_id, date, time, amount, new_balance) 
                VALUES({},'{}','{}',{},{});""".format(accountId, date, time, amount, updatedAmount))

    # updates atm balance to updatedAmount
    def updateATMBalance(self, updatedAmount: int, id: int = 1) -> None:
        self.cursor.execute("UPDATE atm_balance SET balance = {} WHERE Id = {};".format(updatedAmount, id))

    # get the balance of the atm given an id
    def getATMBalanceCmd(self, id: int = 1) -> int:
        self.cursor.execute("SELECT balance FROM atm_balance WHERE Id = {};".format(id))
        data = self.cursor.fetchone()

        # validate that atm data exists, raise exception if it doesn't
        if len(data) > 0:
            balance = data[0]
        else:
            raise Exception("No data exists for atm with id {}.".format(id))

        return balance

    # inserts line to errors table
    def logErrorCmd(self, accountId: int, error: str) -> None:
        try:
            timestamp = datetime.now()

            # if there is no account id then don't insert
            # otherwise insert
            if not accountId:
                self.cursor.execute("""INSERT INTO errors(timestamp, error) 
                                        VALUES('{}', '{}');""".format(timestamp, error))
            else:
                self.cursor.execute("""INSERT INTO errors(account_id, timestamp, error) 
                                        VALUES({}, '{}', '{}');""".format(accountId, timestamp, error))
        # as this is being called from exception block in the controller
        # we need to just aborb the error, most likely a bad sql connection
        except Exception:
            pass
    
    # below methods are just used for testing...

    # get first account
    def getSingleAccountCmd(self) -> Tuple[object]:
        self.cursor.execute("SELECT account_id, pin FROM accounts LIMIT 1;")
        return self.cursor.fetchone()

    # clear account history
    def clearAccountHistoryCmd(self, accountId: int) -> None:
        self.cursor.execute("DELETE FROM history WHERE account_id = {};".format(accountId))