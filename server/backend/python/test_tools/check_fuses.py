#!/usr/bin/env python
"""
//! \brief A script to check if fuses are blown or not
//! \version v2
"""
"""
Output file columns:
| Query MAC | Status |

----------------------------------------------------
    Field        Interpretation
----------------------------------------------------
    offline       Device was offline
    yes           Blown fuses
    no            Not blown fuses
----------------------------------------------------
"""

import sys
import json, requests
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
prod_URL = "https://prod-admin-svc.sleepiq.sleepnumber.com/bam/rest/sn/v1/"
dev21_URL = "https://dev21-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
dev22_URL = "https://dev22-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
dev23_URL = "https://dev23-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
dev24_URL = "https://dev24-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
qa21_URL = "https://qa21-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
qa22_URL = "https://qa22-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
qa23_URL = "https://qa23-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"

backendServer_URL = prod_URL  # CHANGE ME
backendServer_UserName = 'CHANGE_ME'  # CHANGE ME
backendServer_Password = 'CHANGE_ME'  # CHANGE ME
access_token = ''

debug = False  # Enable logging to the console
debugToFile = False  # Enable logging to the file

key = ''
fwrite = ''
lock = ''


def debugging(debug, debugToFile):
    if debugToFile:  # log to file
        logging.basicConfig(
            level=logging.DEBUG,
            format=
            '%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
            datefmt='%a, %d %b %Y %H:%M:%S',
            filename='check_fuses.log',
            filemode='w')
    if debug:  # log to screen
        logging.basicConfig(
            level=logging.DEBUG,
            format=
            '%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
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
    elif server == "prod":
        backendServer_URL = prod_URL
        backendServer_UserName = 'CHANGE_ME'
        backendServer_Password = 'CHANGE_ME'
    else:
        usage()


def check_credentials():
    global backendServer_URL, backendServer_UserName, backendServer_Password, access_token
    if backendServer_URL == "CHANGE_ME" or backendServer_UserName == "CHANGE_ME" \
            or backendServer_Password == "CHANGE_ME":
        print("Please enter valid backend credentials!")
        sys.exit(0)
    headers = {'content-type': 'application/json'}
    credential = {
        "login": backendServer_UserName,
        "password": backendServer_Password
    }
    try:
        test = requests.put(backendServer_URL + 'authenticate?details=true',
                            headers=headers,
                            data=json.dumps(credential))
        test = json.loads(test.text)
        access_token = test["access_token"]
    except Exception as e:
        print("Failed to get access_token: ", str(e))


def getCdcKey(MAC, key):
    global backendServer_URL, access_token
    cdcKey = [{"macAddress": MAC, "cdcKey": key}]
    headers = {'content-type': 'application/json'}
    test = requests.put(backendServer_URL + 'getCdcValues?access_token=' +
                        access_token,
                        headers=headers,
                        data=json.dumps(cdcKey))
    data = json.loads(test.text)

    if data[0]['success']:
        if data[0]['value'] == "":
            if data[0]['failureReason'] is None:
                logging.error(MAC + ":" + key + ":OFFLINE bammcr issue")
            else:
                logging.error(MAC + ":" + key + ":OFFLINE " +
                              str(data[0]['failureReason']))
        else:
            logging.debug(MAC + ":" + key + ":" + data[0]['value'] + '\n')
            return data[0]['value']
    else:
        logging.error(MAC + ":" + key + ":OFFLINE " + data[0]['failureReason'])

    return None


def setCdcKey(MAC, key, value):
    global backendServer_URL, access_token
    cdcKey = [{"macAddress": MAC, "cdcKey": key, "value": value}]
    headers = {'content-type': 'application/json'}
    test = requests.put(backendServer_URL + 'setCdcValues?access_token=' +
                        access_token,
                        headers=headers,
                        data=json.dumps(cdcKey))
    data = json.loads(test.text)

    if data[0]['success']:
        logging.debug(MAC + ":" + key + ":" + data[0]['value'])
        return True
    else:
        logging.error(MAC + ":" + key + ":" + str(value) + ":OFFLINE")
        return False


def check_fuses(line):
    global fwrite, lock
    # Assumed each line contains MAC only
    MAC = line.upper().replace('\n', '')
    MAC = MAC.replace(' ', '')

    key = "LBFG"
    value = getCdcKey(MAC, key)
    if value is None:
        status = "offline"
        value = 0
    else:
        value = int(value)
        if value == 1:
            status = "yes"
        else:
            status = "no"
    print(MAC + "," + status)
    lock.acquire()
    try:
        fwrite.write(MAC + "\t" + status + "\n")
    finally:
        lock.release()


def usage():
    print("python check_fuses.py <server_name> <input_file_name>")
    print("server_name: [c1, c2, alpha, stage, test, prod]")
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
            output_filename = "out_check_fuses_" + sys.argv[1] + "_" + timestamp\
                + "_" + input_filename + ".txt"
            fwrite = open(output_filename, 'w')
            lines = fread.readlines()

            # Create a lock object
            lock = threading.Lock()

            # Make the Pool of workers
            pool = ThreadPool(8)  # CHANGE_ME if needed

            # Open the lines in their own threads and return the results
            results = pool.map(check_fuses, lines)

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

