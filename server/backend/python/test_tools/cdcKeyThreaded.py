#!/usr/bin/env python

"""
//! \brief A script to do backend REST calls for getter BAM keys in multiple
           threads.
//! \version v1
//! \copyright Select Comfort Proprietary and Confidential
//! \copyright Protected by Copyright 2017-2018
"""

import sys
import json, requests
from requests.auth import HTTPBasicAuth
import logging
from multiprocessing.dummy import Pool as ThreadPool

# Backend server address
circle1_URL = "https://circle1-be-api.circle.siq.sleepnumber.com/bam/rest/sn/v1/"
circle2_URL = "https://circle2-be-api.circle.siq.sleepnumber.com/bam/rest/sn/v1/"
genie1_URL = "https://genie1-be-api.siq.sleepnumber.com/bam/rest/sn/v1/"
dev21_URL = "https://dev21-be-api.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
dev22_URL = "https://dev22-be-api.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
dev23_URL = "https://dev23-be-api.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
dev24_URL = "https://dev24-be-api.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
qa21_URL = "https://qa21-be-api.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
qa22_URL = "https://qa22-be-api.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
qa23_URL = "https://qa23-be-api.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
test_URL = "https://test-be-api.siq.sleepnumber.com/bam/rest/sn/v1/"
alpha_URL = "https://alpha-be-api.bamlabs.com/bam/rest/sn/v1/"
stage_URL = "https://stage-be-api.sleepiq.sleepnumber.com/bam/rest/sn/v1/"
prod_URL = "https://prod-be-api.sleepiq.sleepnumber.com/bam/rest/sn/v1/"

backendServer_URL = prod_URL             # CHANGE ME
backendServer_UserName = '*****'         # CHANGE ME
backendServer_Password = '*****'         # CHANGE ME

debug = False           # Enable logging to the console
debugToFile = False     # Enable logging to the file

key = ''
get_type = ''
fwrite = ''


def debugging(debug, debugToFile):
    if debug and debugToFile:  # log to file
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filename='myapp.log',
                            filemode='w')
    if debug:  # log to screen
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S')
    else:
        logging.disable(logging.CRITICAL)


def getCdcKey(line):
    global key, get_type, fwrite
    # Assumed each line contains key only
    MAC = line.upper().replace('\n', '')
    MAC = MAC.replace(' ', '')
    cdcKey = [{"macAddress": MAC, "cdcKey": key}]
    headers = {'content-type': 'application/json'}
    test = requests.put(backendServer_URL + 'getCdcValues', auth=HTTPBasicAuth(backendServer_UserName, backendServer_Password), headers=headers, data=json.dumps(cdcKey))
    data = json.loads(test.text)
    if data[0]['success']:
        if get_type == "gfmac":
            print(MAC + ":" + data[0]['value'])
            fwrite.write(MAC + ":" + data[0]['value'] + '\n')
        else:
            print(key + ":" + data[0]['value'])
            fwrite.write(key + ":" + data[0]['value'] + '\n')
    else:
        if get_type == "gfmac":
            print(MAC + ":FAILURE")
            fwrite.write(MAC + ":FAILURE" + '\n')
        else:
            print(key + ":FAILURE")
            fwrite.write(key + ":FAILURE" + '\n')
    # print(json.dumps(data, indent=4, sort_keys=True))


def setCdcKey(MAC, key, value):
    cdcKey = [{"macAddress": MAC, "cdcKey": key, "value": value}]
    headers = {'content-type': 'application/json'}
    test = requests.put(backendServer_URL + 'setCdcValues', auth=HTTPBasicAuth(backendServer_UserName, backendServer_Password), headers=headers, data=json.dumps(cdcKey))
    data = json.loads(test.text)
    if data[0]['success']:
        print(key + ":" + data[0]['value'])
    else:
        print(key + ":FAILURE")
    # print(json.dumps(data, indent=4, sort_keys=True))


def usage():
    print("python cdcKeyThreaded.py gfmac <MacFileName> <getterKeyName>")


def Main():
    global key, get_type, fwrite
    debugging(debug, debugToFile)       # Call debug method

    if len(sys.argv) == 4 and sys.argv[1] == 'gfmac' \
            and sys.argv[3].isalnum():

        # Device Mac for which we want to do different Rest API calls
        key = sys.argv[3]
        filename = sys.argv[2]
        get_type = sys.argv[1]
        fread = open(filename, 'r')
        fwrite = open("output_key.txt", 'w')
        lines = fread.readlines()

        # Make the Pool of workers
        pool = ThreadPool(4)            # CHANGE ME if needed

        # Open the lines in their own threads and return the results
        results = pool.map(getCdcKey, lines)

        # close the pool and wait for the work to finish
        pool.close()
        pool.join()

    else:
        usage()


if __name__ == '__main__':
    Main()
