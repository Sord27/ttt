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
from datetime import date, datetime, timedelta
import calendar
from backendservercheck import serverCheck

# from datetime import timedelta
# from datetime import datetime, timedelta




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
# MAC = "64dba0000018"

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

    todayDate = time.strftime("%m/%d/%y")  # check
    my_date = date.today()
    dayOftheweek = calendar.day_name[my_date.weekday()]
    dayOftheweek = dayOftheweek.lower()
    # Get yesterday date and in the RSOD formate
    yesterdayDate = date.today() - timedelta(1)
    yesterDayOfTheweek = calendar.day_name[yesterdayDate.weekday()]
    yesterDayOfTheweek = yesterDayOfTheweek.lower()
    yesterdayDate = yesterdayDate.strftime('%m/%d/%y')
    dateToCheck = ""
    dayToCheck = ""
    timelimit = r'(?:(0[0-9]|1[0-9]|2[0-3]))'

    start= 13
    start = str(start)
    print(start[1])

    '''
    if start <= 9:
        timelimit = r'(?:(0['+ str(start) + r'-9]|1[0-9]|2[0-3]))'
    if start => 10:
        timelimit = '(?:(1[0-9]|2[0-3]))'
    if start = >20:
        timelimit = '(?:(2[0-3]))'
    '''
    #timelimit = "\d\d"
    # print("\n",timelimit)


    # child.sendline("uptime")
    # child.expect('#')
    # logging.debug(child.before)
    # logging.debug(child.after)

    child.sendline("cat /bam/etc/preferences")
    child.expect(':~#')
    # logging.debug(child.before)
    # logging.debug(child.after)
    preferences = child.before
    preferences = preferences.decode()
    #logging.debug(preferences)

    # 05/15/17 21:30:02 Skipped changing left side due to sleeper already in bed
    # 05/15/17 21:30:33 Skipped changing right side due to sleeper already in bed

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
            find_ra_Right_activities = re.compile(re.escape(todayDate) + '(\s.*\sR\sadj\s+\d+\-\>\s\d+)')
            ra_Today_Right_activities = find_ra_Right_activities.findall(ra_activities)
            print(ra_Today_Right_activities)
            ra_Today_Right_activities_count = len(ra_Today_Right_activities)
            print(ra_Today_Right_activities_count)

            yesterdayfind_ra_Right_activities = re.compile((re.escape(yesterdayDate)) + '(\s)' + (timelimit) + '(:\d\d:\d\d\sR\sadj\s+\d+\-\>\s\d+)')
            #yesterdayfind_ra_Right_activities = re.compile(re.escape(yesterdayDate) + '(\s\d\d:\d\d:\d\d\sR\sadj\s+\d+\-\>\s\d+)')
            yesterdayra_Right_activities = yesterdayfind_ra_Right_activities.findall(ra_activities)
            print(yesterdayra_Right_activities)
            yesterdayra_Right_activities_count = len(yesterdayra_Right_activities)
            print(yesterdayra_Right_activities_count)

            totalR = ra_Today_Right_activities_count + yesterdayra_Right_activities_count
            print("\n\n total: %d",totalR)




        if ra_Left_Status == "true":
            find_ra_Left_activities = re.compile(re.escape(getDate) + '(\s.*\sL\sadj\s+\d+\-\>\s\d+)')
            ra_Left_activities = find_ra_Left_activities.findall(ra_activities)
            print(ra_Left_activities)
            ra_Left_activities_count = len(ra_Left_activities)
            print(ra_Left_activities_count)

            yesterdayfind_ra_Left_activities = re.compile(re.escape(yesterdayDate) + '(\s)' + timelimit + '(:\d\d:\d\d\sL\sadj\s+\d+\-\>\s\d+)')
            yesterdayra_Left_activities = yesterdayfind_ra_Left_activities.findall(ra_activities)
            print(yesterdayra_Left_activities)
            yesterdayra_Left_activities_count = len(yesterdayra_Left_activities)
            print(yesterdayra_Left_activities_count)

            totalL = ra_Left_activities_count + yesterdayra_Left_activities_count
            print("\n\n total: %d", totalL)



    else:
        ra_Right_activities_count = 0
        ra_Left_activities_count = 0
    print("\n")
    #print(total)
    print(ra_Left_activities_count)
    #activities_count = find_ra_activities.findall(ra_activities)
    #print(len(activities_count))
    #print(activities_count)
   ## dd/mm/yyyy format
    print(date)

    
    

    

    

   
    yesterday = date.today() - timedelta(1)
    print("\n")
    yesterday = yesterday.strftime('%m/%d/%y')
    print(yesterday)

    child.sendline("logout")
    child.expect('$')

# child.sendline("exit")
# child.expect('~]$')

# child.logout()
print(1)
