#!/usr/bin/env python

"""
//! \brief A script to do backend REST calls for getter/setter BAM keys
//! \version v1
//! \copyright Select Comfort Proprietary and Confidential
//! \copyright Protected by Copyright 2017-2018
"""

import sys
import json, requests
from requests.auth import HTTPBasicAuth
import logging

# Backend server address
circle1_URL = "https://circle1-admin-svc.circle.siq.sleepnumber.com/bam/rest/sn/v1/"
circle2_URL = "https://circle2-admin-svc.circle.siq.sleepnumber.com/bam/rest/sn/v1/"
genie1_URL = "https://genie1-be-api.siq.sleepnumber.com/bam/rest/sn/v1/"
dev21_URL = "https://dev21-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
dev22_URL = "https://dev22-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
dev23_URL = "https://dev23-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
dev24_URL = "https://dev24-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
qa21_URL = "https://qa21-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
qa22_URL = "https://qa22-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
qa23_URL = "https://qa23-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
test_URL = "https://test-admin-svc.siq.sleepnumber.com/bam/rest/sn/v1/"
alpha_URL = "https://alpha-admin-svc.bamlabs.com/bam/rest/sn/v1/"
stage_URL = "https://stage-admin-svc.stage.siq.sleepnumber.com/bam/rest/sn/v1/"
prod_URL = "https://prod-admin-svc.sleepiq.sleepnumber.com/bam/rest/sn/v1/"

backendServer_URL = circle1_URL          # CHANGE ME
backendServer_UserName = '*****'         # CHANGE ME
backendServer_Password = '*****'         # CHANGE ME

debug = False           # Enable logging to the console
debugToFile = False     # Enable logging to the file


def debugging(debug, debugToFile):
    if debug and debugToFile:  # log to file
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(filename)s \
                            %(funcName)s(): %(lineno)d:\t %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filename='myapp.log',
                            filemode='w')
    if debug:  # log to screen
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(filename)s \
                            %(funcName)s(): %(lineno)d:\t %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S')
    else:
        logging.disable(logging.CRITICAL)


def getCdcKey(MAC, key, get_type):
    cdcKey = [{"macAddress": MAC, "cdcKey": key}]
    headers = {'content-type': 'application/json'}
    test = requests.put(backendServer_URL + 'getCdcValues', auth=HTTPBasicAuth(
                        backendServer_UserName, backendServer_Password),
                        headers=headers, data=json.dumps(cdcKey))
    data = json.loads(test.text)
    if data[0]['success']:
        if get_type == "gfmac":
            print(MAC + ":" + data[0]['value'])
        else:
            print(key + ":" + data[0]['value'])
    else:
        if get_type == "gfmac":
            print(MAC + ":FAILURE")
        else:
            print(key + ":FAILURE")
    # print(json.dumps(data, indent=4, sort_keys=True))


def setCdcKey(MAC, key, value):
    cdcKey = [{"macAddress": MAC, "cdcKey": key, "value": value}]
    headers = {'content-type': 'application/json'}
    test = requests.put(backendServer_URL + 'setCdcValues', auth=HTTPBasicAuth(
                        backendServer_UserName, backendServer_Password),
                        headers=headers, data=json.dumps(cdcKey))
    data = json.loads(test.text)
    if data[0]['success']:
        print(key + ":" + data[0]['value'])
    else:
        print(key + ":FAILURE")
    # print(json.dumps(data, indent=4, sort_keys=True))


def usage():
    print("python cdcKey.py g <Mac> <getterKeyName>")
    print("python cdcKey.py gfkey <Mac> <getterKeysFileName>")
    print("python cdcKey.py gfmac <MacFileName> <getterKeyName>")
    print("python cdcKey.py s <Mac> <setterKeyName> <setterKeyValue>")


def Main():
    debugging(debug, debugToFile)       # Call debug method
    if len(sys.argv) == 4 and sys.argv[1] == 'g' and sys.argv[2].isalnum() \
            and sys.argv[3].isalnum():

        # Device Mac for which we want to do different Rest API calls
        mac = sys.argv[2]
        key = sys.argv[3]
        getCdcKey(mac, key, sys.argv[1])

    elif len(sys.argv) == 4 and sys.argv[1] == 'gfkey' \
            and sys.argv[2].isalnum():

        # Device Mac for which we want to do different Rest API calls
        mac = sys.argv[2]
        filename = sys.argv[3]
        fread = open(filename, 'r')
        # fwrite = open('getterKeys_output.txt', 'w')
        for line in fread:
            # Assumed each line contains key only
            key = line.replace('\n', '')
            key = key.replace(' ', '')
            getCdcKey(mac, key, sys.argv[1])

    elif len(sys.argv) == 4 and sys.argv[1] == 'gfmac' \
            and sys.argv[3].isalnum():

        # Device Mac for which we want to do different Rest API calls
        key = sys.argv[3]
        filename = sys.argv[2]
        fread = open(filename, 'r')
        # fwrite = open('getterKeys_output.txt', 'w')
        for line in fread:
            # Assumed each line contains key only
            mac = line.upper().replace('\n', '')
            mac = mac.replace(' ', '')
            getCdcKey(mac, key, sys.argv[1])

    elif len(sys.argv) == 5 and sys.argv[1] == 's' and sys.argv[2].isalnum() \
            and sys.argv[3].isalnum():

        # Device Mac for which we want to do different Rest API calls
        mac = sys.argv[2]
        key = sys.argv[3]
        value = sys.argv[4]
        setCdcKey(mac, key, value)
    else:
        usage()


if __name__ == '__main__':
    Main()
