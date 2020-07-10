from Classes.ATM import ATM
from Classes.ControllerResponse import ControllerResponse

if __name__ == "__main__":
    atmObj = ATM()
    end = False
    print("Welcome to ATM-Bot 2000. Please enter a command!\n")

    # keep accepting user input until end command is given
    while not end:
        usrInput = input()
        response = atmObj.controller(usrInput)

        # print message if it exists
        if response.message:
            print("{}\n".format(response.message))
        
        # update end flag base on response
        end = response.end