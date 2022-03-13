#!/usr/bin/env python3

"""
//! \brief A script to query pumps using CDC calls to the backend
//! \version v1
//! \copyright Select Comfort Proprietary and Confidential
//! \copyright Copyright 2018, All Rights Reserved
"""

"""
A utility script to GET or SET a key on a pump 

"""

import sys
import json
import logging
import os
import requests
import argparse
from requests.auth import HTTPBasicAuth
import http.client as http_client

VERSION = "0.1.0"
backendServer_URL = None
backendServer_UserName = None
backendServer_Password = None

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def debugging(debug, debugToFile):
    # enable HTTP library (http_client and requests) logging if we ask for "--debug"
    if debug:
        http_client.HTTPConnection.debuglevel = 1
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    if debugToFile:  # log to file
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filename='cdc.log',
                            filemode='w')

    if debug:  # log to screen
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S')
    else:
        logging.disable(logging.CRITICAL)

def check_credentials():
    global backendServer_URL, backendServer_UserName, backendServer_Password
    if backendServer_URL == "xxxxx" or backendServer_UserName == "xxxxx" \
            or backendServer_Password == "xxxxx":
        print("Please enter valid backend credentials!")
        sys.exit(-1)

#
# Given a device_id (MAC address), query the server for the given bio key and display the result
# from the server to the user on the console
#
def getCdcKey(device_id, key):
    global backendServer_URL, backendServer_UserName, backendServer_Password
    cdcKey = [{"macAddress": device_id.upper(), "cdcKey": key.upper()}]
    headers = {'content-type': 'application/json'}
    url = backendServer_URL + '/getCdcValues'
    print("PUT {} data = {}".format(url, json.dumps(cdcKey,separators=(',',':'))))
    data = None
    try:
        test = requests.put(url, auth=HTTPBasicAuth(backendServer_UserName, backendServer_Password), headers=headers, data=json.dumps(cdcKey))
        logging.debug(test.text)
        data = json.loads(test.text)
    except Exception as err:
        print(err)

    if data != None:
        print(json.dumps(data, sort_keys=True, indent=2))
    else:
        print(test.text)

    return None

#
# Given a device_id (MAC address), tell the server to set the given bio key/value and display the result
# from the server to the user on the console
#
def setCdcKey(device_id, key, value):
    global backendServer_URL, backendServer_UserName, backendServer_Password
    cdcKey = [{"macAddress": device_id.upper(), "cdcKey": key.upper(), "value": value}]
    headers = {'content-type': 'application/json'}
    url = backendServer_URL + '/setCdcValues'
    print("PUT {} data = {}".format(url, json.dumps(cdcKey,separators=(',',':'))))
    test = requests.put(url, auth=HTTPBasicAuth(backendServer_UserName, backendServer_Password), headers=headers, data=json.dumps(cdcKey))
    data = json.loads(test.text)

    if data != None:
        print(json.dumps(data, sort_keys=True, indent=2))
    else:
        print(test)

    return None

def Main():
    global fwrite, backendServer_UserName, backendServer_URL, backendServer_Password
    parser = argparse.ArgumentParser(description='CDC utility.')
    parser.add_argument('device_id', metavar='<device_id>', type=str,
                        help='The mac address of the device to operate upon')
    parser.add_argument('key', metavar='<key>', type=str, help='The bio key to send')
    parser.add_argument('--env', nargs='?', default="circle1", help='set the server environment, circle1 default [circle1, circle2, test, stage, ...]')
    parser.add_argument('--set', action='store_true', help='PUT /setCdcValues call, otherwise we assume this is a GET')
    parser.add_argument('--value', nargs='?', help='PUT /setCdcValues call, otherwise we assume this is a GET')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug logging')
    parser.add_argument('--debugToFile', action='store_true', help='Enable debug logging to file')
    args = parser.parse_args()

    CONFIG_JSON = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__), "config.json"))
    try:
        env = json.load(open(CONFIG_JSON))[args.env]
    except Exception as err:
        print(err)
        print("ERROR: could not load config.json")
        sys.exit(-1)

    backendServer_URL = env['admin-svc']
    backendServer_UserName = env['backoffice']['username']
    backendServer_Password = env['backoffice']['password']
    check_credentials()
    logging.debug("Accessing {} user {}".format(backendServer_URL, backendServer_UserName))

    # setup debugging
    debugging(args.debug, args.debugToFile)

    if (args.set == True):
        value = args.value
        setCdcKey(args.device_id, args.key, value)
    else:
        getCdcKey(args.device_id, args.key)

if __name__ == '__main__':
    Main()
