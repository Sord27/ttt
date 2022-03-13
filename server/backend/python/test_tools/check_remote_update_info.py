#!/usr/bin/env python3

"""
//! \brief A script to collect 360 remote update information
//! \version v1
"""

"""
Output file columns:
| Query MAC | Status |

----------------------------------------------------
    Field        Interpretation
----------------------------------------------------
    error         Got exception while processing device
    NA            Device was offline
    <number1>     Successful remote updates
    <number2>     Not successful remote updates
    <number3>     Failure percentage if any
    <number4>     Current progress percentage if any
----------------------------------------------------
"""

import sys
import json, requests
from requests.auth import HTTPBasicAuth
import logging
import threading
from multiprocessing.dummy import Pool as ThreadPool
import datetime
import os

# Backend admin services
circle1_URL = "https://circle1-admin-svc.circle.siq.sleepnumber.com/bam/rest/sn/v1/"
circle2_URL = "https://circle2-admin-svc.circle.siq.sleepnumber.com/bam/rest/sn/v1/"
test_URL = "https://test-admin-svc.siq.sleepnumber.com/bam/rest/sn/v1/"
alpha_URL = "https://alpha-admin-svc.bamlabs.com/bam/rest/sn/v1/"
stage_URL = "https://stage-admin-svc.stage.siq.sleepnumber.com/bam/rest/sn/v1/"
ux_URL = "https://ux-admin-svc.ux.siq.sleepnumber.com/bam/rest/sn/v1/"
prod_URL = "https://prod-admin-svc.sleepiq.sleepnumber.com/bam/rest/sn/v1/"
dev21_URL = "https://dev21-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
dev22_URL = "https://dev22-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
dev23_URL = "https://dev23-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
dev24_URL = "https://dev24-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
qa21_URL = "https://qa21-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
qa22_URL = "https://qa22-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
qa23_URL = "https://qa23-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"


backendServer_URL = prod_URL            # CHANGE ME
backendServer_UserName = 'CHANGE_ME'    # CHANGE ME
backendServer_Password = 'CHANGE_ME'    # CHANGE ME

debug = False           # Enable logging to the console
debugToFile = False     # Enable logging to the file

key = ''
fwrite = ''
lock = ''


def debugging(debug, debugToFile):
    if debugToFile:  # log to file
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filename='check_remote_update_info.log',
                            filemode='w')
    if debug:  # log to screen
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S')
    else:
        logging.disable(logging.CRITICAL)


def set_backend_credentials(server):
    global backendServer_URL, backendServer_UserName, backendServer_Password
    if server == "c1":
        backendServer_URL = circle1_URL
        backendServer_UserName = 'CHANGE_ME'
        backendServer_Password = 'CHANGE_ME'
    elif server == "c2":
        backendServer_URL = circle2_URL
        backendServer_UserName = 'CHANGE_ME'
        backendServer_Password = 'CHANGE_ME'
    elif server == "test":
        backendServer_URL = test_URL
        backendServer_UserName = 'CHANGE_ME'
        backendServer_Password = 'CHANGE_ME'
    elif server == "alpha":
        backendServer_URL = alpha_URL
        backendServer_UserName = 'CHANGE_ME'
        backendServer_Password = 'CHANGE_ME'
    elif server == "stage":
        backendServer_URL = stage_URL
        backendServer_UserName = 'CHANGE_ME'
        backendServer_Password = 'CHANGE_ME'
    elif server == "ux":
        backendServer_URL = ux_URL
        backendServer_UserName = 'CHANGE_ME'
        backendServer_Password = 'CHANGE_ME'
    elif server == "prod":
        backendServer_URL = prod_URL
        backendServer_UserName = 'CHANGE_ME'
        backendServer_Password = 'CHANGE_ME'
    else:
        usage()


def check_credentials():
    global backendServer_URL, backendServer_UserName, backendServer_Password
    if backendServer_URL == "CHANGE_ME" or backendServer_UserName == "CHANGE_ME" \
            or backendServer_Password == "CHANGE_ME":
        print("Please enter valid backend credentials!")
        sys.exit(0)


def getCdcKey(MAC, key):
    global backendServer_URL, backendServer_UserName, backendServer_Password
    cdcKey = [{"macAddress": MAC, "cdcKey": key}]
    headers = {'content-type': 'application/json'}
    test = requests.put(backendServer_URL + 'getCdcValues', auth=HTTPBasicAuth(backendServer_UserName, backendServer_Password), headers=headers, data=json.dumps(cdcKey))
    data = json.loads(test.text)

    if data[0]['success']:
        if data[0]['value'] == "":
            if data[0]['failureReason'] is None:
                logging.error(MAC + ":" + key + ":OFFLINE bammcr issue")
            else:
                logging.error(MAC + ":" + key + ":OFFLINE " + str(data[0]['failureReason']))
        else:
            logging.debug(MAC + ":" + key + ":" + data[0]['value'] + '\n')
            return data[0]['value']
    else:
        logging.error(MAC + ":" + key + ":OFFLINE " + data[0]['failureReason'])

    return None


def setCdcKey(MAC, key, value):
    global backendServer_URL, backendServer_UserName, backendServer_Password
    cdcKey = [{"macAddress": MAC, "cdcKey": key, "value": value}]
    headers = {'content-type': 'application/json'}
    test = requests.put(backendServer_URL + 'setCdcValues', auth=HTTPBasicAuth(backendServer_UserName, backendServer_Password), headers=headers, data=json.dumps(cdcKey))
    data = json.loads(test.text)

    if data[0]['success']:
        logging.debug(MAC + ":" + key + ":" + data[0]['value'])
        return True
    else:
        logging.error(MAC + ":" + key + ":" + str(value) + ":OFFLINE")
        return False


def check_remote_update_info(line):
    global fwrite, lock
    # Assumed each line contains MAC only
    MAC = line.upper().replace('\n', '')
    MAC = MAC.replace(' ', '')

    key = "PRUI"
    try:
        value = getCdcKey(MAC, key)
        success, failure, failure_percentage, progress_percentage = "NA", "NA", "NA", "NA"
        if value is None:
            value = 0
        else:
            success, failure, failure_percentage, progress_percentage = value.split(" ")
        print(MAC + "," + success + "," + failure
                + "," + failure_percentage + "," + progress_percentage)
        lock.acquire()
        try:
            fwrite.write(MAC + "\t" + success + "\t" + failure
                + "\t" + failure_percentage + "\t" + progress_percentage + "\n")
        finally:
            lock.release()
    except Exception as e:
        success, failure, failure_percentage, progress_percentage = "error", "error", "error", "error"
        print(MAC + "," + str(e))
        lock.acquire()
        try:
            fwrite.write(MAC + "\t" + success + "\t" + failure
                    + "\t" + failure_percentage + "\t" + progress_percentage + "\n")
        finally:
            lock.release()


def usage():
    print("python3 check_remote_update_info.py <server_name> <input_file_name>")
    print("server_name: [c1, c2, alpha, stage, test, ux, prod]")
    sys.exit(0)


def Main():
    global fwrite, lock
    debugging(debug, debugToFile)

    if len(sys.argv) == 3:
        set_backend_credentials(sys.argv[1])
        check_credentials()
        input_filename = sys.argv[2]
        if os.path.isfile(input_filename):
            fread = open(input_filename, 'r')
            timestamp = datetime.datetime.now().strftime("%y%m%d%H%M")
            output_filename = "out_check_remote_update_info_" + sys.argv[1] + "_" + timestamp\
                + "_" + input_filename + ".txt"
            fwrite = open(output_filename, 'w')
            lines = fread.readlines()

            # Create a lock object
            lock = threading.Lock()

            # Make the Pool of workers
            pool = ThreadPool(8)            # CHANGE_ME if needed

            # Open the lines in their own threads and return the results
            results = pool.map(check_remote_update_info, lines)

            # close the pool and wait for the work to finish
            pool.close()
            pool.join()
            fwrite.close()
            fread.close()

            # Sort output file
            command = "sort " + output_filename + " -o " + output_filename
            os.system(command)
        else:
            print("Input file doesn't exist!")
            usage()
    else:
        usage()


if __name__ == '__main__':
    Main()
