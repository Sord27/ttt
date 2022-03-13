#!/usr/bin/env python3

"""
//! \brief A script to query pumps and turn on footwarming pads (if not already on) and then read back values to find LCTE events.
//! \version v1
//! \copyright Select Comfort Proprietary and Confidential
//! \copyright Copyright 2018, All Rights Reserved
"""

"""
A utility script to query a pump regarding RSO for BAM-7943

Mike Puckett created a bio command device side from which I based the logic flow used in this script for
off-device (server) side use.

This script can run multiple threads so you can get results from a large number of pumps more quickly.

"""

import sys
import jira
import json
import logging
import datetime
import os
import time
import requests
import argparse
from requests.auth import HTTPBasicAuth
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import Lock

VERSION = "0.1.2"
JIRA_URL= "http://jira.bamlabs.com:8080"
JIRA_TICKET="BAM-7943"
REPLACE_ME = "xxxxx"
fwrite_lock = Lock()
fwrite = None

FW_TEMP_OFF    = 0
FW_TEMP_LOW    = 31
FW_TEMP_MEDIUM = 57
FW_TEMP_HIGH   = 72
FW_TEMP_TIME=120

SIDE_RIGHT = "0"
SIDE_LEFT = "1"
SIDES = ["R", "L"]

def debugging(debug, debugToFile):
    if debugToFile:  # log to file
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filename='rso.log',
                            filemode='w')
    if debug:  # log to screen
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S')
    else:
        logging.disable(logging.CRITICAL)

def check_credentials():
    global backendServer_URL, backendServer_UserName, backendServer_Password
    if backendServer_URL == REPLACE_ME or backendServer_UserName == REPLACE_ME \
            or backendServer_Password == REPLACE_ME:
        print("Please enter valid backend credentials!")
        sys.exit(-1)

def parse_key_response(device_id, data, key):
    if data[0]['success']:
        if data[0]['value'] == "":
            logging.debug(data)
            if data[0]['failureReason'] is None:
                logging.debug(device_id + ":" + key + ":OFFLINE bammcr issue")
            else:
                logging.debug(device_id + ":" + key + ":OFFLINE " +
                              str(data[0]['failureReason']))
        else:
            logging.debug(device_id + ":" + key + ":" + data[0]['value'] + '\n')
            return data[0]['value']
    else:
        logging.debug(device_id + ":" + key + ":OFFLINE " + data[0]['failureReason'])

def getCdcKey(device_id, key):
    global backendServer_URL, backendServer_UserName, backendServer_Password
    cdcKey = [{"macAddress": device_id.upper(), "cdcKey": key.upper()}]
    headers = {'content-type': 'application/json'}
    url = backendServer_URL + '/getCdcValues'
    logging.debug("getCdcKey {} data = {}".format(url, json.dumps(cdcKey,separators=(',',':'))))
    data = None
    try:
        test = requests.put(url, auth=HTTPBasicAuth(backendServer_UserName, backendServer_Password), headers=headers, data=json.dumps(cdcKey))
        logging.debug(test.text)
        data = json.loads(test.text)
    except Exception as err:
        print(err)
        data = [{'key':key, 'value' : None}]
    return data

def setCdcKey(device_id, key, value):
    global backendServer_URL, backendServer_UserName, backendServer_Password
    cdcKey = [{"macAddress": device_id.upper(), "cdcKey": key.upper(), "value": value}]
    headers = {'content-type': 'application/json'}
    url = backendServer_URL + '/setCdcValues'
    logging.debug("setCdcKey {} data = {}".format(url, json.dumps(cdcKey,separators=(',',':'))))
    data = None
    try:
        test = requests.put(url, auth=HTTPBasicAuth(backendServer_UserName, backendServer_Password), headers=headers, data=json.dumps(cdcKey))
        data = json.loads(test.text)
    except Exception as err:
        print(err)

    if data[0]['success']:
        logging.debug(device_id + ":" + key + ":" + data[0]['value'])
        return True
    else:
        logging.debug(device_id + ":" + key + ":" + str(value) + ":OFFLINE")
        return False

def fnd_available(device_id):
    data = getCdcKey(device_id, 'MPXY')[0]['value']
    devices = int(data[0:2])
    logging.debug("{} MPXY {}".format(device_id, json.dumps(data, separators=(',', ':'))))
    if devices & 0x04:
        logging.debug("{} Foundation Present".format(device_id))
        return True
    else:
        logging.warning("{} No Foundation Present".format(device_id))
        return False


# By the time we get here, we know that we're on a 360 connected
# to a foundation.  To determine whether there are RSO pads connected
# to it, we make the foundation self-check call, specifically asking
# about the RSO pads.  So, it's key MFCK and arg 8.  That's the setter.
# The corresponding getter is MFCG.  Since we're only asking about
# the RSO pads, we just want to extract their information from the
# entire string that is returned.  In this case, we want to know
# whether the test we asked about finished or not, and if so, what
# were its results.
#
# Determine if BOTH left and right footpads are connected. We only return true if they are.
#
def rso_pads_connected(device_id):
    # Issue the setter.  This could fail.  But we won't be able to tell
    # until we do the corresponding getter.
    #
    value = setCdcKey(device_id, "MFCK", "8")
    logging.debug("{} MFCK {}".format(device_id, str(value)))

    # Wait a second before issuing the getter.  It's performing a self-check,
    # which should take less than a second.  But give a chance not to fail.
    #
    time.sleep(1)

    # Now, issue the getter.
    #
    data = getCdcKey(device_id, "MFCG")
    logging.debug("{} MFCG {}".format(device_id, json.dumps(data,separators=(',',':'))))

    # If the getter didn't fail outright (meaning the 360 foundation might
    # have not responded to our request), then we can check to see what
    # it returned.
    value = data[0]['value']
    is_successful = value[0:2] == "02"
    if is_successful == False:
        logging.error("MFCG not successful")
        return False
    foot_pads = int(value[6:8])
    if (foot_pads == 3): # Left connected and Right connected (bit 0 is right and bit 1 is left)
        return True
    else:
        return False

# Return the level (FWGx returns level and timer value as "0 0")
def get_footwarming(device_id, side):
    value = None
    if (side == SIDE_RIGHT):
        value = getCdcKey(device_id, "FWGR")[0]['value'].split(' ')[0]
    else:
        value = getCdcKey(device_id, "FWGL")[0]['value'].split(' ')[0]
    return int(value)

# Validate data and send it to the output routine
def validate_and_write_data(device_id, mafr_value, mafl_value, mafe_value):
    MAFX_EXPECTED_COUNT = 7
    MAFE_EXPECTED_COUNT = 4

    if len(mafr_value.split(' ')) != MAFX_EXPECTED_COUNT:
        logging.error("{} MAFR returned incorrect number of values: '{}'".format(device_id, mafr_value))
        return

    if len(mafl_value.split(' ')) != MAFX_EXPECTED_COUNT:
        logging.error("{} MAFL returned incorrect number of values: '{}'".format(device_id, mafl_value))
        return

    if len(mafe_value.split(' ')) != MAFE_EXPECTED_COUNT:
        logging.error("{} MAFE returned incorrect number of values: '{}'".format(device_id, mafe_value))
        return

    line_out = device_id + "\t" + "\t".join(mafr_value.split(' '))  + "\t" + "\t".join(mafl_value.split(' '))  + "\t" + "\t".join(mafe_value.split(' '))
    write_output(line_out)

def write_output(line_out):
    global fwrite, fwrite_lock

    line_csv = ",".join(line_out.split("\t"))
    logging.debug(line_csv)
    print(line_csv)

    fwrite_lock.acquire()
    try:
        fwrite.write(line_out + "\n")
    finally:
        fwrite_lock.release()  # release lock, no matter what

def set_footwarming(device_id, side, setting):
    if (side == SIDE_RIGHT):
        return setCdcKey(device_id, "FWSR", setting)
    else:
        return setCdcKey(device_id, "FWSL", setting)

# This is the main worker unit fed by the thread manager; each pertains to one line of the input filename or one
# device for processing and output.
#
def process_line(line):
    #is this a comment or empty?
    if line[0:1] == '#' or len(line) == 0:
        logging.debug("skipping comment|empty line '{}'".format(line))
        return

    # Parse the line into the parameters we need
    #
    # Assumed each line contains MAC
    line = line.split('\t')
    device_id = line[0].upper().replace('\n', '').replace(' ', '').replace(':', '')

    try:
        # Check if foundation is available
        if fnd_available(device_id):
            if rso_pads_connected(device_id) == False:
                logging.warning(device_id + ",x,x,x,footwarmers not available")
                return # stop processing this line

            # To proceed, we're going to look at both pads.  First, we check
            # to see whether they are on or not.  If they are on, we'll read
            # their data immediately.  If they are not on, we'll turn them
            # on, remember that we did so, wait 60 seconds, read their data,
            # and then turn them off.  We'll do the right side first then
            # the left side.

            # To see whether the pads are on or not, we use the FWGR and
            # FWGL keys. We already have functions for these from the
            # rsod_config functions library.  So, we'll use those.

            turn_off_r = 0
            turn_off_l = 0
            mafr_value = 0
            mafl_value = 0

            # If the right pad isn't off, get its data.
            #
            if get_footwarming(device_id, SIDE_RIGHT) != FW_TEMP_OFF:
                mafr_value = getCdcKey(device_id, "MAFR")[0]['value']
                logging.debug("{} RSO already on; MAFR: {}".format(device_id, mafr_value))
                if mafr_value == None: # if call failed, skip logging this device
                    return
            else:
                # Turn on the right pad at the low temperature.  Don't
                # pass a timeout value and it'll default to six hours,
                # but we're going to turn it off shortly.
                #
                if set_footwarming(device_id, SIDE_RIGHT, FW_TEMP_LOW) == False:
                    return; # error so do not continue
                turn_off_r = 1

            # Ditto for the left side
            if get_footwarming(device_id, SIDE_LEFT) != FW_TEMP_OFF:
                mafl_value = getCdcKey(device_id, "MAFL")[0]['value']
                if mafl_value == None: # if call failed, skip logging this device
                    return
                logging.debug("{} RSO already on; MAFL: {}".format(device_id, mafl_value))

            else:
                # Turn on the right pad at the low temperature.  Don't
                # pass a timeout value and it'll default to six hours,
                # but we're going to turn it off shortly.
                #
                if set_footwarming(device_id, SIDE_LEFT, FW_TEMP_LOW) == False:
                    return; # error so do not continue
                turn_off_l = 1

            # If one or both of the pads weren't on, wait a minute,
            # read their data, and turn them off.  Redo the reads
            # in this case so that it's more reflective of them both
            # being on at the same time (at least for the minute that
            # they were likely both still on).
            #
            if turn_off_r == 1 or turn_off_l == 1:
                secs = 59
                while secs >= 0:
                    logging.debug("waiting seconds<{:02}> for the LCT data...\r".format(secs))
                    time.sleep(1)
                    secs -= 1

            # Get right/left side data
            mafr_value = getCdcKey(device_id, 'MAFR')[0]['value']
            logging.debug("{} MAFR {}".format(device_id, mafr_value))
            if mafr_value == None: # if call failed, skip logging this device
                return

            mafl_value = getCdcKey(device_id, 'MAFL')[0]['value']
            logging.debug("{} MAFL {}".format(device_id, mafl_value))
            if mafl_value == None: # if call failed, skip logging this device
                return

            if turn_off_r == 1:
                set_footwarming(device_id, SIDE_RIGHT, FW_TEMP_OFF)

            if turn_off_l == 1:
                set_footwarming(device_id, SIDE_LEFT, FW_TEMP_OFF)

            # We also want to check the MAFE values right away and flag it if this turning on of the footwarming
            # pads has triggered and LCTE event or not.
            mafe_value = getCdcKey(device_id, 'MAFE')[0]['value']
            logging.debug("{} MAFE {}".format(device_id, json.dumps(mafe_value, separators=(',', ':'))))
            if mafe_value == None: # if call failed, skip logging this device
                return

            # pass the data for validation and output
            validate_and_write_data(device_id, mafr_value, mafl_value, mafe_value)
        else:
            logging.warning(device_id + ",x,x,x,FND offline/not available")
    except Exception as e:
        logging.error(device_id + ",x,x,x,Exception:" + str(e))

# in progress method for attaching result file to a JIRA ticket.
def jira_attach_file(jira_url, ticket, filename):
    logging.info("Attaching {} to {}".format(filename, ticket))
    options = {
        'server': jira_url
    }
    try:
        jira_client = jira.JIRA(options=options, basic_auth=(os.environ['JIRA_USERNAME'], os.environ['JIRA_PASSWORD']))
        issue = jira_client.issue(ticket)
        attachment = jira_client.add_attachment(issue, attachment=filename)
        logging.info("Attachment done")
    except Exception as err:
        logging.error("ERROR accessing JIRA")

def Main():
    global fwrite, backendServer_UserName, backendServer_URL, backendServer_Password

    # Ok, first up let's parse out the command line options
    parser = argparse.ArgumentParser(description='LCT BAM-7943 CDC Utility.')
    parser.add_argument('--env', nargs='?', default="circle1", help='set the server environment')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug logging')
    parser.add_argument('--attach', required=False, help='Add the result file to a JIRA ticket')
    parser.add_argument('--debugToFile', '-D', action='store_true', help='Enable debug logging to file')
    parser.add_argument('--threads', required=False, help='Enable debug logging to file')
    parser.add_argument('input_filename', metavar='<input_filename>', type=str, help='The file that contains the list of mac addresses to operate upon')
    args = parser.parse_args()
    print(args)

    # Load environment variables from config.json
    CONFIG_JSON = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__), "config.json"))
    try:
        env = json.load(open(CONFIG_JSON))[args.env]
    except Exception as err:
        print(err)
        print("ERROR: could not load config.json")
        sys.exit(-1)

    # Set some globals for which server to access via HTTP
    backendServer_URL = env['admin-svc']
    backendServer_UserName = env['backoffice']['username']
    backendServer_Password = env['backoffice']['password']

    # Make sure the credentials aren't placeholders (exits app if they are)
    check_credentials()

    # Setup debugging based on CLI parameters
    debugging(args.debug, args.debugToFile)

    # Log which URL and user we are using
    logging.debug("Accessing {} user {}".format(backendServer_URL, backendServer_UserName))

    if os.path.isfile(args.input_filename):
        fread = open(args.input_filename, 'r')
        timestamp = datetime.datetime.now().strftime("%y%m%d%H%M")
        output_filename = "{}_{}_output.tsv".format(args.input_filename, timestamp)
        fwrite = open(output_filename, 'w')
        lines = fread.readlines()

        # Make the Pool of workers
        if args.threads == None:
            args.threads = "4"
        pool = ThreadPool(int(args.threads))            # CHANGE ME if needed

        # Open the lines in their own threads and return the results
        results = pool.map(process_line, lines)

        # close the pool and wait for the work to finish
        pool.close()
        pool.join()
        fwrite.close()
        fread.close()

        # Sort output file
        command = "sort " + output_filename + " -o " + output_filename
        os.system(command)

        if args.attach != None and len(args.attach) > 0:
            jira_attach_file(JIRA_URL, JIRA_TICKET, output_filename)
    else:
        print("Input file doesn't exist!")

if __name__ == '__main__':
    Main()
