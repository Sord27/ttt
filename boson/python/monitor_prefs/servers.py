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
    payload = json.dumps({"macAddress": str(MAC), "unixCommand": "pkill ssh"})
    logging.debug(payload)

    AccountID = ""
    DeviceID = ""

    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s ')

    # Get the account ID
    test = requests.get(backendServer_URL + 'filteredUsers?filterByString=' + str(MAC),
                        auth=HTTPBasicAuth(backendServer_UserName, backendServer_Password), headers=headers)
    data = json.loads(test.text)
    logging.debug(json.dumps(data, indent=4, sort_keys=True))
    logging.debug("\n")
    if len(data["results"]) == 0:  # Mac not found in the server, json returned empty result
        logging.debug("The MAC address provided is not registered with the server.")
        return 0
    numberToLoop = len(data["results"])
    for i in range(numberToLoop):  # check for condition where
        if data["results"][i]["macAddress"] == MAC:  # we could have more than one accountID
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
        if data["results"][i]["macAddress"] == MAC:  # If the accoundID contains more
            DeviceID = data["results"][i]["deviceId"]  # than one MAC addresse, get the one we are
            logging.debug("DeviceID ==>" + str(DeviceID))  # after.
            break

            # Get the device status

    test = requests.get(
        backendServer_URL + 'account/' + str(AccountID) + '/device/' + str(DeviceID) + '/bedCurrentStatus',
        auth=HTTPBasicAuth(backendServer_UserName, backendServer_Password), headers=headers)
    data = json.loads(test.text)
    logging.debug(json.dumps(data, indent=4, sort_keys=True))
    logging.debug("\n")
    if data["status"] == 1:  # if the device live in the server send RPC to kill all open SHH sesssions.
        test = requests.post(backendServer_URL + 'deviceRPC',
                             auth=HTTPBasicAuth(backendServer_UserName, backendServer_Password), headers=headers,
                             data=payload)
        data = json.loads(test.text)
        logging.debug(json.dumps(data, indent=4, sort_keys=True))
        logging.debug("\nkilled all open SSH session")
        return 1
    else:
        logging.debug(json.dumps(data, indent=4, sort_keys=True))
        return 2  # Device exists in the backend server but it is offline.


def getUsers(MAC, backendServer_URL, backendServer_UserName, backendServer_Password):
    headers = {'content-type': 'application/json'}
    test = requests.get(backendServer_URL + 'filteredUsers?filterByString=' + str(MAC),
                        auth=HTTPBasicAuth(backendServer_UserName, backendServer_Password), headers=headers)
    data = json.loads(test.text)
    logging.debug(json.dumps(data, indent=4, sort_keys=True))
    logging.debug("\n")
    if len(data["results"]) == 0:  # Mac not found in the server, json returned empty result
        logging.debug("The MAC address provided is not registered with the server.")
        return "Not in production"
    # Get the first user Available
    userInfo = str(
        "F:" + data["results"][0]["firstName"] + ",L:" + data["results"][0]["lastName"] + ",E:" + data["results"][0][
            "login"])
    return userInfo


def findBeServere(MAC):
    user = "hassan@bamlabs.com"
    password= "Test1234"
    credential = []
    headers = {'content-type': 'application/json'}

    # Checking the MAC against the production server
    test = requests.get('https://prod-be-api.sleepiq.sleepnumber.com/bam/rest/sn/v1/' + 'filteredUsers?filterByString=' + str(MAC), auth=HTTPBasicAuth(user, password), headers=headers)
    data = json.loads(test.text)
    print(json.dumps(data, indent=4, sort_keys=True))
    if len(data["results"]) != 0:
        credential.append('https://prod-be-api.sleepiq.sleepnumber.com/bam/rest/sn/v1/')
        credential.append(user)
        credential.append(password)
        return credential

    # Checking the MAC against the Test server
    test = requests.get('https://test-be-api.siq.sleepnumber.com/bam/rest/sn/v1/' + 'filteredUsers?filterByString=' + str(MAC), auth=HTTPBasicAuth(user, password), headers=headers)
    data = json.loads(test.text)
    print(json.dumps(data, indent=4, sort_keys=True))
    if len(data["results"]) != 0:
        credential.append('https://test-be-api.siq.sleepnumber.com/bam/rest/sn/v1/')
        credential.append(user)
        credential.append(password)
        return credential
    # Checking the MAC against the Stage server
    test = requests.get('https://stage-be-api.siq.sleepnumber.com/bam/rest/sn/v1/' + 'filteredUsers?filterByString=' + str(MAC), auth=HTTPBasicAuth(user, password), headers=headers)
    data = json.loads(test.text)
    print(json.dumps(data, indent=4, sort_keys=True))
    if len(data["results"]) != 0:
        credential.append('https://stage-be-api.siq.sleepnumber.com/bam/rest/sn/v1/')
        credential.append(user)
        credential.append(password)
        return credential

    # Checking the MAC against the Circle1 server
    test = requests.get('https://circle1-be-api.circle.siq.sleepnumber.com/bam/rest/sn/v1/' + 'filteredUsers?filterByString=' + str(MAC),auth=HTTPBasicAuth(user, password), headers=headers)
    data = json.loads(test.text)
    if len(data["results"]) != 0:
        credential.append('https://circle1-be-api.circle.siq.sleepnumber.com/bam/rest/sn/v1/')
        credential.append(user)
        credential.append(password)
        return credential

    # Checking the MAC against the Circle2 server
    test = requests.get('https://circle2-be-api.circle.siq.sleepnumber.com/bam/rest/sn/v1/' + 'filteredUsers?filterByString=' + str(
            MAC), auth=HTTPBasicAuth(user, password), headers=headers)
    data = json.loads(test.text)
    if len(data["results"]) != 0:
        credential.append('https://circle2-be-api.circle.siq.sleepnumber.com/bam/rest/sn/v1/')
        credential.append(user)
        credential.append(password)
        return credential

    # MAC address not found in any server
    return credential


def validate():
    data = json.loads(test.text)
    print(json.dumps(data, indent=4, sort_keys=True))
    print("\n")
    logging.debug(json.dumps(data, indent=4, sort_keys=True))
    logging.debug("\n")


if __name__ == '__main__':
    # MAC = "CC04B408F0F2"
    #MAC = "CC04B408A20F"
    MAC = "64DBA0000228"
    #MAC = "64dba00002d8"
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s ')
    backendServer_URL = "https://prod-be-api.sleepiq.sleepnumber.com/bam/rest/sn/v1/"
    backendServer_UserName = "hassan@bamlabs.com"
    backendServer_Password = "Test1234"
    # returnValueTest = serverCheck(MAC, backendServer_URL, backendServer_UserName, backendServer_Password)
    # returnValueTest = getUsers(MAC, backendServer_URL, backendServer_UserName, backendServer_Password)
    testcr = findBeServere(MAC)
    print(len(testcr))
    print("\n")
    print(testcr[0])
    print("\n")
    print(testcr[1])
    print("\n")
    print(testcr[2])
    print("\n")
    print(len(testcr))
    # print(returnValueTest)

'''
qa21      https://qa21-be-api.dev.siq.sleepnumber.com/bam/rest/sn/v1/version
qa22      https://qa22-be-api.dev.siq.sleepnumber.com/bam/rest/sn/v1/version
qa23      https://qa23-be-api.dev.siq.sleepnumber.com/bam/rest/sn/v1/version
dev21    https://dev21-be-api.dev.siq.sleepnumber.com/bam/rest/sn/v1/version
dev22    https://dev22-be-api.dev.siq.sleepnumber.com/bam/rest/sn/v1/version
dev23    https://dev23-be-api.dev.siq.sleepnumber.com/bam/rest/sn/v1/version
dev24    https://dev24-be-api.dev.siq.sleepnumber.com/bam/rest/sn/v1/version
genie1  https://genie1-be-api.siq.sleepnumber.com/bam/rest/sn/v1/version
circle1   https://circle1-be-api.circle.siq.sleepnumber.com/bam/rest/sn/v1/version
circle2   https://circle2-be-api.circle.siq.sleepnumber.com/bam/rest/sn/v1/version
test        https://test-be-api.siq.sleepnumber.com/bam/rest/sn/v1/version
alpha     https://alpha-be-api.bamlabs.com/bam/rest/sn/v1/version
stage     "https://stage-be-api.sleepiq.sleepnumber.com/bam/rest/sn/v1/version
//https://admin-stage.siq.sleepnumber.com (BE APIs- qa001@qa.com)"
prod      https://prod-be-api.sleepiq.sleepnumber.com/bam/rest/sn/v1/version
//
'''
