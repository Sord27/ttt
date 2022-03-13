#!/usr/bin/env python

"""
//! \brief A script to check RSO(foot-warming pads) connectivity for given
           device list.
//! \version v2
//! \copyright Select Comfort Proprietary and Confidential
//! \copyright Protected by Copyright 2017-2018
"""

"""
Output file columns:
| Query MAC | Order Number | RSO Left | RSO Right | Status |

----------------------------------------------------
    Field        Interpretation
----------------------------------------------------
      Y          Left/Right connected
      N          Left/Right disconnected
      x          Error with failure reason
----------------------------------------------------
"""

import sys
import json, requests
from requests.auth import HTTPBasicAuth
import logging
from multiprocessing.dummy import Pool as ThreadPool
import datetime
import os

# Backend server address
circle1_URL = "https://circle1-admin-svc.circle.siq.sleepnumber.com/bam/rest/sn/v1/"
circle2_URL = "https://circle2-admin-svc.circle.siq.sleepnumber.com/bam/rest/sn/v1/"
genie1_URL = "https://genie1-be-api.siq.sleepnumber.com/bam/rest/sn/v1/"
dev21_URL = "https://dev21-be-api.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
dev22_URL = "https://dev22-be-api.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
dev23_URL = "https://dev23-admin-svc.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
dev24_URL = "https://dev24-be-api.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
qa21_URL = "https://qa21-be-api.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
qa22_URL = "https://qa22-be-api.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
qa23_URL = "https://qa23-be-api.dev.siq.sleepnumber.com/bam/rest/sn/v1/"
test_URL = "https://test-admin-svc.siq.sleepnumber.com/bam/rest/sn/v1/"
alpha_URL = "https://alpha-admin-svc.bamlabs.com/bam/rest/sn/v1/"
stage_URL = "https://stage-admin-svc.stage.siq.sleepnumber.com/bam/rest/sn/v1/"
prod_URL = "https://prod-admin-svc.sleepiq.sleepnumber.com/bam/rest/sn/v1/"

backendServer_URL = prod_URL             # CHANGE ME
backendServer_UserName = 'xxxxx'         # CHANGE ME
backendServer_Password = 'xxxxx'         # CHANGE ME

debug = False           # Enable logging to the console
debugToFile = False     # Enable logging to the file

key = ''
fwrite = ''
default_order_no = "99999999999"


def debugging(debug, debugToFile):
    if debugToFile:  # log to file
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filename='RSO_connectivity.log',
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
        backendServer_UserName = 'xxxxx'
        backendServer_Password = 'xxxxx'
    elif server == "c2":
        backendServer_URL = circle2_URL
        backendServer_UserName = 'xxxxx'
        backendServer_Password = 'xxxxx'
    elif server == "test":
        backendServer_URL = test_URL
        backendServer_UserName = 'xxxxx'
        backendServer_Password = 'xxxxx'
    elif server == "alpha":
        backendServer_URL = alpha_URL
        backendServer_UserName = 'xxxxx'
        backendServer_Password = 'xxxxx'
    elif server == "stage":
        backendServer_URL = stage_URL
        backendServer_UserName = 'xxxxx'
        backendServer_Password = 'xxxxx'
    elif server == "prod":
        backendServer_URL = prod_URL
        backendServer_UserName = 'xxxxx'
        backendServer_Password = 'xxxxx'
    else:
        usage()


def check_credentials():
    global backendServer_URL, backendServer_UserName, backendServer_Password
    if backendServer_URL == "xxxxx" or backendServer_UserName == "xxxxx" \
            or backendServer_Password == "xxxxx":
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
            logging.debug(data)
            if data[0]['failureReason'] is None:
                #print(MAC + ":" + key + ":OFFLINE bammcr issue" + )
                logging.debug(MAC + ":" + key + ":OFFLINE bammcr issue")
            else:
                #print(MAC + ":" + key + ":OFFLINE " + str(data[0]['failureReason']))
                logging.debug(MAC + ":" + key + ":OFFLINE " + str(data[0]['failureReason']))
        else:
            #print(MAC + ":" + key + ":" + data[0]['value'])
            logging.debug(MAC + ":" + key + ":" + data[0]['value'] + '\n')
            return data[0]['value']
    else:
        #print(MAC + ":" + key + ":OFFLINE " + data[0]['failureReason'])
        logging.debug(MAC + ":" + key + ":OFFLINE " + data[0]['failureReason'])

    return None


def setCdcKey(MAC, key, value):
    global backendServer_URL, backendServer_UserName, backendServer_Password
    cdcKey = [{"macAddress": MAC, "cdcKey": key, "value": value}]
    headers = {'content-type': 'application/json'}
    test = requests.put(backendServer_URL + 'setCdcValues', auth=HTTPBasicAuth(backendServer_UserName, backendServer_Password), headers=headers, data=json.dumps(cdcKey))
    data = json.loads(test.text)

    if data[0]['success']:
        #print(MAC + ":" + key + ":" + data[0]['value'])
        logging.debug(MAC + ":" + key + ":" + data[0]['value'])
        return True
    else:
        #print(MAC + ":" + key + ":" + str(value) + ":OFFLINE")
        logging.debug(MAC + ":" + key + ":" + str(value) + ":OFFLINE")
        return False


def fnd_available(MAC):
    value = getCdcKey(MAC, 'MPXY')
    if value is not None and value[0:2] == "04":
        return True
    else:
        return False


def check_RSO(line):
    global fwrite
    # Assumed each line contains MAC and order number only
    line = line.split('\t')
    # Check if MAC and order number both are available otherwise set default
    # order number
    if len(line) == 2:
        line, order_no = line[0], line[1]
    else:
        line, order_no = line[0], default_order_no
    MAC = line.upper().replace('\n', '')
    MAC = MAC.replace(' ', '')
    order_no = order_no.replace('\n', '')
    order_no = order_no.replace(' ', '')

    # Check if foundation is available
    if fnd_available(MAC):
        # Run foot warming self check test
        if setCdcKey(MAC, 'MFCK', 8):
            # Get Foot warming pad info
            value = getCdcKey(MAC, 'MFCG')
            if value is not None:
                foot_pads = value[6:8]
                # Left connected and Right connected
                if foot_pads == "03":
                    print(MAC + "," + order_no + ",Y,Y,Success")
                    fwrite.write(MAC + "\t" + order_no + "\tY\tY\tSuccess" + '\n')
                # Left connected and Right not connected
                elif foot_pads == "02":
                    print(MAC + "," + order_no + ",Y,N,Success")
                    fwrite.write(MAC + "\t" + order_no + "\tY\tN\tSuccess" + '\n')
                # Left not connected and Right connected
                elif foot_pads == "01":
                    print(MAC + "," + order_no + ",N,Y,Success")
                    fwrite.write(MAC + "\t" + order_no + "\tN\tY\tSuccess" + '\n')
                # Left not connected and Right not connected
                elif foot_pads == "00":
                    print(MAC + "," + order_no + ",N,N,Success")
                    fwrite.write(MAC + "\t" + order_no + "\tN\tN\tSuccess" + '\n')
                # Unexpected value
                else:
                    print(MAC + "," + order_no + ",x,x,Unknown")
                    fwrite.write(MAC + "\t" + order_no + "\tx\tx\tUnknown" + '\n')
            else:
                print(MAC + "," + order_no + ",x,x,Error in getting MFCG")
                fwrite.write(MAC + "\t" + order_no + "\tN\tN\tError in getting MFCG" + '\n')
        else:
            print(MAC + "," + order_no + ",x,x,Error in setting MFCK")
            fwrite.write(MAC + "\t" + order_no + "\tN\tN\tError in setting MFCK" + '\n')
    else:
        print(MAC + "," + order_no + ",x,x,FND offline/not available")
        fwrite.write(MAC + "\t" + order_no + "\tx\tx\tFND offline/not available" + '\n')


def usage():
    print("python RSO_connectivity.py <server_name> <input_file_name>")
    print("server_name: [c1, c2, alpha, stage, test, prod]")
    sys.exit(0)


def Main():
    global fwrite
    debugging(debug, debugToFile)

    if len(sys.argv) == 3:
        set_backend_credentials(sys.argv[1])
        check_credentials()
        input_filename = sys.argv[2]
        if os.path.isfile(input_filename):
            fread = open(input_filename, 'r')
            timestamp = datetime.datetime.now().strftime("%y%m%d%H%M")
            output_filename = "RSO_connectivity_" + sys.argv[1] + "_" + timestamp + ".txt"
            fwrite = open(output_filename, 'w')
            lines = fread.readlines()

            # Make the Pool of workers
            pool = ThreadPool(4)            # CHANGE ME if needed

            # Open the lines in their own threads and return the results
            results = pool.map(check_RSO, lines)

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
