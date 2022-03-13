'''
Connect to Boson server
Author: Hassan Zaidan
Date: 04/20/2017
This part of script will initiate and process the necessary components to connect Boson server.
As well SSHing to the individual devices. The return values for each function described below.
Optionally debug can be turned on.

Return values
Get_PxsshObj
s = retrun object connected to Boson server
1 = Execpetion had happen retrun to exit code

get_device
0 = Accessed the device
1=  Device does not exists in the backend server
2 = Device is offline
3 = device taking too long to recover skip
4 = Error end of file expection
5 = Error TIMEOUT
6 = Unkwon execpetion
'''

import pexpect
from pexpect import pxssh
import sys, os
import logging
import json, requests
from requests.auth import HTTPBasicAuth
import string
import re
import time
from datetime import date,datetime, timedelta
import calendar
from backendservercheck import serverCheck
#from datetime import timedelta
#from datetime import datetime, timedelta




AccountID = ""  # Store the account ID
DeviceID = ""  # Store the devive ID


def debugging(debug, debugToFile):
    if debug == True and debugToFile == True:  # log to file
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filename='myapp.log',
                            filemode='w')
    if debug == True:  # log to screen
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S')

    else:
        logging.disable(logging.CRITICAL)


def Get_PxsshObj(bosonServer, bosonUser, bosonPassword, bosonPort, bosonPrompt, bosonTimeout, bosonSSHKEY):
    try:
        s = pxssh.pxssh()
        i = s.login(bosonServer, bosonUser, password=bosonPassword, port=bosonPort, original_prompt=bosonPrompt,
                    login_timeout=bosonTimeout, ssh_key=bosonSSHKEY)

        if i == True:
            s.sendline('uptime')
            test_server = s.expect(['load'])
            if test_server == 0:
                print("Connected to Boson and ready to access devices:")
                logging.debug(s.before)
                logging.debug(s.after)
                logging.debug(s.buffer)
                return s
            else:
                logging.debug('Connected to Boson, but cannot access devices!?')
                return 1

    except pexpect.ExceptionPexpect as e:
        logging.debug(e)
        logging.debug(
            "An exception error had occured, cannot login into Boson, please check credintial, network or private key")
        return 1


# -------------------------------------------------------------------------------------------------------------------

def get_Device(child, MAC, backendServer_URL, backendServer_UserName, backendServer_Password):
    testcase1 = "ECDSA key fingerprint is "
    testcase2 = "password:"
    testcase3 = "No CSTAT entry found in NFS, looping."
    try_limit = 0
    try:
        while try_limit <= 1:
            child.sendline('sessh -f ' + MAC)
            test_device = child.expect([testcase1, testcase2, testcase3, pexpect.EOF, pexpect.TIMEOUT])
            if test_device == 0:
                child.sendline("yes")
                if child.expect("password") == 0:
                    child.sendline("bam!ssh")
                if child.expect("#") == 0:
                    return 0
            elif test_device == 1:
                child.sendline("bam!ssh")
                if child.expect("#") == 0:
                    return 0
            elif test_device == 2:
                logging.debug("Device not found, sending Control-C")
                child.sendcontrol("C")
                if child.expect("$") == 0 & try_limit < 1:
                    foundDevice = serverCheck(MAC, backendServer_URL, backendServer_UserName, backendServer_Password)
                    if foundDevice == 0:
                        logging.debug("device does not exists")
                        return 1
                    elif foundDevice == 1:
                        time.sleep(60)  # Wait for one minutes for the SSH to restart
                        try_limit = try_limit + 1
                        continue
                    elif foundDevice == 2:
                        return 2
                else:
                    return 3  # SHH taking too long to start skip this device

                    # ---------------------------
            elif test_device == 3:
                logging.debug("Error device sent ENF")
                return 4
            elif test_device == 4:
                logging.debug("Error device timed out")
                return 5

    except pexpect.ExceptionPexpect as e:
        logging.debug(e)
        logging.debug("Unkown exception error had occured, cannot login into device: " + MAC)
        return 6


# --------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    '''Boson Parameters'''
    bosonServer = 'devices.dev.siq.sleepnumber.com'
    bosonUser = 'hassan'
    bosonPassword = 'nura6719'
    bosonPort = '6022'
    bosonPrompt = '[#|$]'
    bosonTimeout = 10
    bosonSSHKEY = '/home/hassan/sshkey/mypkey4'
'''Backend Parameters'''
userName = "hassan@bamlabs.com"
password = "Test1234"
backendServerURL = "https://prod-be-api.sleepiq.sleepnumber.com/bam/rest/sn/v1/"

MAC = "64DBA0000071"
#MAC = "64dba0000018"

debug = True
debugToFile = False
debugging(debug, debugToFile)

logging.debug('start of program')
child = Get_PxsshObj(bosonServer, bosonUser, bosonPassword, bosonPort, bosonPrompt, bosonTimeout, bosonSSHKEY)
if child == 1:
    print("Unable to establish connection with Boson server exiting program:")
    sys.exit()
device = get_Device(child, MAC, backendServerURL, userName, password)
if device == 0:
    getDate = time.strftime("%m/%d/%y")  # check
    my_date = date.today()
    dayOftheweek = calendar.day_name[my_date.weekday()]
    dayOftheweek = dayOftheweek.lower()
    print(dayOftheweek)

   # child.sendline("uptime")
    #child.expect('#')
    #logging.debug(child.before)
    #logging.debug(child.after)

    child.sendline("cat /bam/etc/preferences")
    child.expect(':~#')
    # logging.debug(child.before)
    # logging.debug(child.after)
    preferences = child.before
    preferences = preferences.decode()
    logging.debug(preferences)

    #05/15/17 21:30:02 Skipped changing left side due to sleeper already in bed
    #05/15/17 21:30:33 Skipped changing right side due to sleeper already in bed
    '''#block////////////////////////////////////////////////////////////////////////////////////////////////
    ############ra = preferences.decode()
    ra_Right = re.search(r'(^ra_right_enable=)(.*)(\r\r$)', preferences, re.M)
    ra_Right_Status = ra_Right.group(2)
    print(ra_Right_Status)
    ra_Left = re.search(r'(^ra_left_enable=)(.*)(\r\r$)', preferences, re.M)
    ra_Left_Status = ra_Left.group(2)
    print(ra_Left_Status)

    if ra_Right_Status == "true" or ra_Left_Status == "true":
        child.sendline("bio rad")   
        child.expect(':~#')
        ra_activities = child.before
        ra_activities = ra_activities.decode()
        if ra_Right_Status == "true":
            find_ra_Right_activities = re.compile(re.escape(getDate) + '(\s.*\sR\sadj\s+\d+\-\>\s\d+)')
            ra_Right_activities = find_ra_Right_activities.findall(ra_activities)
            print(ra_Right_activities)
            ra_Right_activities_count = len(ra_Right_activities)
            print(ra_Right_activities_count)

        if ra_Left_Status == "true":
            find_ra_Left_activities = re.compile(re.escape(getDate) + '(\s.*\sL\sadj\s+\d+\-\>\s\d+)')
            ra_Left_activities = find_ra_Left_activities.findall(ra_activities)
            print(ra_Left_activities)
            ra_Left_activities_count = len(ra_Left_activities)
            print(ra_Left_activities_count)

    else:
        ra_Right_activities_count = 0
        ra_Left_activities_count = 0
    print("\n")
    print(ra_Right_activities_count)
    print(ra_Left_activities_count)
    #activities_count = find_ra_activities.findall(ra_activities)
    #print(len(activities_count))
    #print(activities_count)
   ## dd/mm/yyyy format
    print(date)
    '''  # block//////////////////////////////////////////////////////////////////////////////////////////
    '''
    underBedLight = re.search(r'(^ul_auto_enabled=)(.*)(\r\r\n)', preferences, re.M)
    if underBedLight.group(2) == "true":
        # ouPutSheet['E' + str(row)].value = "Y"print("\nnumber of ons %d",NumberoflightTurnedOn)
        print("\n Underned light is enabled ")
        print(underBedLight.group(2))
        child.sendline("bio ul_logs")
        child.expect(':~#')
        ul_logs = child.before
        ul_logs = ul_logs.decode()
        #logging.debug(preferences)
        lightTurnedOn = re.compile(re.escape(getDate) + '(\s\d\d:\d\d:\d\d\sset underbed to 1 for\s)')
        NumberoflightTurnedOn = lightTurnedOn.findall(ul_logs)
        NumberoflightTurnedOn = len(NumberoflightTurnedOn)
        # outPutSheet['E' + str(row)].value = "N"
        print("\n Number of light turned on ")
        print(NumberoflightTurnedOn)
        lightTurnedOff = re.compile(re.escape(getDate) + '(\s\d\d:\d\d:\d\d\sturned off underbed)')
        NumberoflightTurnedOff = lightTurnedOff.findall(ul_logs)
        NumberoflightTurnedOff = len(NumberoflightTurnedOff)
        # outPutSheet['E' + str(row)].value = "N"
        print("\n Number of light turned off ")
        print(NumberoflightTurnedOff)
        print("\nnumber of ons %d", NumberoflightTurnedOn)
        print("\nnumber of ons %d", NumberoflightTurnedOff)

    else:
        # outPutSheet['E' + str(row)].value = "N"
        # outPutSheet['E' + str(row)].value = "-"
        # outPutSheet['E' + str(row)].value = "-"
        print("\n Underbed light disabled ")
        lightTurnedOff = re.compile(re.escape(getDate) + '(\s\d\d:\d\d:\d\d\sturned off underbed)')
    '''
    #print(datetime.date.today() - datetime.timedelta(1))
    child.sendline("bio rsod")
    child.expect(':~#') #change
    rsod = child.before
    rsod = rsod.decode()
    footWarmingRight = re.search(r'(^br_right_)' + (re.escape(dayOftheweek)) + r'(_enabled=)(.*)(\r\r\n)', preferences, re.M)
    print("\n\n")
    print(footWarmingRight.group(3))
    if footWarmingRight.group(3) == "true":
        # outPutSheet['V' + str(row)].value = "Y"
        '''print("Right e=side is true\n")
        find_rsod_Right_Activities = re.compile(re.escape(getDate) + '(\s\d\d:\d\d:\d\d\sSet\sright\sside\sto\s)([^0]\d*)(\r\r\n)')
        rsod_Right_Activities = find_rsod_Right_Activities.findall(rsod)
        print(len(rsod_Right_Activities))
        '''

        find_rsod_Right_Activities = re.compile(re.escape(getDate))  # ([^0]\d*)(\r\r\n)
        rsod_Right_Activities = find_rsod_Right_Activities.findall(rsod)
        print(rsod_Right_Activities)
        print(len(rsod_Right_Activities))

        find_rsod_Right_Activities = re.compile(re.escape(getDate) +'(\s\d\d:\d\d:\d\d\sSet\sright\sside\sto\s)([^0]\d*)')#([^0]\d*)(\r\r\n)
        '''re.escape(getDate)+'''
        rsod_Right_Activities = find_rsod_Right_Activities.findall(rsod)
        print(rsod_Right_Activities)
        print(len(rsod_Right_Activities))

        find_rsod_Right_Activities = re.compile(re.escape(getDate) + '(\s\d\d:\d\d:\d\d\sSet\sright\sside\sto\s)(0.*)')  # ([^0]\d*)(\r\r\n)
        rsod_Right_Activities = find_rsod_Right_Activities.findall(rsod)
        print(rsod_Right_Activities)
        print(len(rsod_Right_Activities))

        find_rsod_Right_Activities = re.compile(re.escape(getDate))  # ([^0]\d*)(\r\r\n)
        rsod_Right_Activities = find_rsod_Right_Activities.findall(rsod)
        print(rsod_Right_Activities)
        print(len(rsod_Right_Activities))


        # 05/15/17 21:30:02 Skipped changing left side due to sleeper already in bed
        # 05/15/17 21:30:33 Skipped changing right side due to sleeper already in bed

    else:
        # outPutSheet['V' + str(row)].value = "N"
        print("Right side is false\n")




    '''
    Underbed original 
    underBedLight = re.search(r'(^ul_auto_enabled=)(.*)(\r\r\n)', preferences, re.M)
    if underBedLight == "true":
        #ouPutSheet['E' + str(row)].value = "Y"print("\nnumber of ons %d",NumberoflightTurnedOn)
        print("\n Underned light is enabled ")
        underBedLightRight = re.search(r'(^br_right_)' + (re.escape(dayOftheweek)) + r'(_enabled=)(.*)(\r\r\n)', preferences, re.M)
        if underBedLightRight == "true":
            #ouPutSheet['E' + str(row)].value = "Y"
            print("\n Underned light right side is enabled ")
        else:
            # ouPutSheet['E' + str(row)].value = "N"
            print("\n Underned light right side is Off ")

        underBedLightLeft = re.search(r'(^br_left_)' + (re.escape(dayOftheweek)) + r'(_enabled=)(.*)(\r\r\n)', preferences, re.M)
        if underBedLightLeft == "true":
            #ouPutSheet['E' + str(row)].value = "Y"
            print("\n Underned light Left side is enabled ")
        else:
            # ouPutSheet['E' + str(row)].value = "N"
            print("\n Underned light Lefy side is Off ")

        if underBedLightRight == "true" or underBedLightLeft == "true":
            child.sendline("bio ul_logs")
            child.expect(':~#')
            ul_logs = child.before
            ul_logs = ul_logs.decode()
            logging.debug(preferences)
            lightTurnedOn = re.compile(re.escape(getDate) + '(\s\d\d:\d\d:\d\d\sset underbed to 1 for\s)')
            NumberoflightTurnedOn = lightTurnedOn.findall(ul_logs)

            lightTurnedOff = re.compile(re.escape(getDate) + '(\s\d\d:\d\d:\d\d\sturned off underbed)')
            NumberoflightTurnedOff = lightTurnedOff.findall(ul_logs)

            print("\nnumber of ons %d",NumberoflightTurnedOn)
            print("\nnumber of ons %d",NumberoflightTurnedOff)

    else:
        #outPutSheet['E' + str(row)].value = "N"
        print("\n Underbed light disabled ")
        
     '''



    '''
    ra_Right = re.search(r'(^br_right_)' + (re.escape(dayOftheweek)) + r'(_enabled=)(.*)(\r\r\n)', fw, re.M)

    print("\n here we start -------------")
    print("\n Group 0")
    print(ra_Right.group(0))
    print("\n Group 1")
    print(ra_Right.group(1))
    print("\nGroup 2")
    print(ra_Right.group(2))
    print("\nGroup 3")
    print(ra_Right.group(3))
    print("\nGroup 4")
    print(ra_Right.group(4))

    print("\nGroup 5")
    print(ra_Right.group(4))

    ra_Left = re.search(r'(^br_left_)' + (re.escape(dayOftheweek)) + r'(_enabled=)(.*)(\r\r\n)', fw, re.M)

    print("\n here we start -------------")
    print("\n Group 0")
    print(ra_Left.group(0))
    print("\n Group 1")
    print(ra_Left.group(1))
    print("\nGroup 2")
    print(ra_Left.group(2))
    print("\nGroup 3")
    print(ra_Left.group(3))
    print("\nGroup 4")
    print(ra_Left.group(4))

    print("\nGroup 5")
    print(ra_Right.group(4))
    '''

        # ul_auto_enabled = true

    # +(_enabled\s =\s(. *)(\r\r$))'

    #print(datetime.date.today() - datetime.timedelta(1))
    # print(datetime.datetime.now() - datetime.timedelta(days=1))
    #####print(("%m/%d/%y", date.today() - timedelta(1)))
    yesterday = date.today() - timedelta(1)
    print("\n")
    yesterday= yesterday.strftime('%m/%d/%y')
    print(yesterday)

    child.sendline("logout")
    child.expect('$')

# child.sendline("exit")
# child.expect('~]$')

# child.logout()
print(1)
