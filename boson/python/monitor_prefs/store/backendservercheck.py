''
Connect to Backend server
Author: Hassan Zaidan
Date: 04/20/2017
This part of script will initiate and process the necessary components to connect to the Backend server to check
if the device is off line or it is overwhelmed with SSH connections . It tries to fix the issue by killing all
open SSH currently that open on the device and wait for 60 seconds for SSH to restart.
The return values as described below.

Return values
0 = The MAC address provided is not registered with the current backend server
1 = Device online with overwhelmed open SSH sesssions
2 = Device is offline
'''

import json, requests
import logging
from requests.auth import HTTPBasicAuth

def serverCheck(MAC, backendServer_URL, backendServer_UserName, backendServer_Password):

    headers = {'content-type': 'application/json'}
    payload = json.dumps({"macAddress" : str(MAC), "unixCommand" : "pkill ssh"})
    logging.debug(payload)


    AccountID =""
    DeviceID = ""

    #logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s ')

# Get the account ID
    test = requests.get(backendServer_URL  + 'filteredUsers?filterByString=' + str(MAC), auth=HTTPBasicAuth(backendServer_UserName, backendServer_Password), headers=headers)
    data = json.loads(test.text)
    logging.debug(json.dumps(data, indent=4, sort_keys=True))
    logging.debug("\n")
    if len(data["results"])==0: # Mac not found in the server, json returned empty result
        logging.debug("The MAC address provided is not registered with the server.")
        return 0
    numberToLoop = len(data["results"])
    for i in range(numberToLoop):                        # check for condition where
        if data["results"][i]["macAddress"] == MAC:      # we could have more than one accountID
            AccountID = data["results"][i]["accountId"]  # under customerID
            logging.debug(" found AccountID ==>" + str(AccountID))
            break


# Get the device ID
    test = requests.get(backendServer_URL + 'account/' + str(AccountID) + '/devices',
                        auth=HTTPBasicAuth(backendServer_UserName, backendServer_Password), headers=headers)

    data = json.loads(test.text)
    logging.debug(json.dumps(data, indent=4, sort_keys=True))
    logging.debug("\n")
    numberToLoop = len(data["results"])
    for i in range(numberToLoop):
        if data["results"][i]["macAddress"] == MAC:       # If the accoundID contains more
            DeviceID = data["results"][i]["deviceId"]     # than one MAC addresse, get the one we are
            logging.debug("DeviceID ==>" + str(DeviceID)) # after.
            break

# Get the device status

    test = requests.get(backendServer_URL + 'account/' + str(AccountID) + '/device/' + str(DeviceID ) + '/bedCurrentStatus',auth=HTTPBasicAuth(backendServer_UserName, backendServer_Password), headers=headers)
    data = json.loads(test.text)
    logging.debug(json.dumps(data, indent=4, sort_keys=True))
    logging.debug("\n")
    if data["status"] == 1: # if the device live in the server send RPC to kill all open SHH sesssions.
        test = requests.post(backendServer_URL + 'deviceRPC', auth=HTTPBasicAuth(backendServer_UserName, backendServer_Password), headers=headers,data=payload)
        data = json.loads(test.text)
        logging.debug(json.dumps(data, indent=4, sort_keys=True))
        logging.debug("\nkilled all open SSH session")
        return 1
    else:
        logging.debug(json.dumps(data, indent=4, sort_keys=True))
        return 2 # Device exists in the backend server but it is offline.



def getUsers(MAC, backendServer_URL, backendServer_UserName, backendServer_Password):
    headers = {'content-type': 'application/json'}
    test = requests.get(backendServer_URL + 'filteredUsers?filterByString=' + str(MAC),auth=HTTPBasicAuth(backendServer_UserName, backendServer_Password), headers=headers)
    data = json.loads(test.text)
    logging.debug(json.dumps(data, indent=4, sort_keys=True))
    logging.debug("\n")
    if len(data["results"]) == 0:  # Mac not found in the server, json returned empty result
        logging.debug("The MAC address provided is not registered with the server.")
        return "Not in production"
    #Get the first user Available
    userInfo = str("F:" + data["results"][0]["firstName"] + ",L:" +  data["results"][0]["lastName"] + ",E:" + data["results"][0]["login"])
    return userInfo


if __name__ == '__main__':
    #MAC = "CC04B408F0F2"
    MAC = "CC04B408A20F"
    #MAC = "64DBA0000228"
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s ')
    backendServer_URL = "https://prod-be-api.sleepiq.sleepnumber.com/bam/rest/sn/v1/"
    backendServer_UserName = "hassan@bamlabs.com"
    backendServer_Password = "Test1234"
    #returnValueTest = serverCheck(MAC, backendServer_URL, backendServer_UserName, backendServer_Password)
    returnValueTest = getUsers(MAC, backendServer_URL, backendServer_UserName, backendServer_Password)
    print("\n")
    print(returnValueTest)
