#!/usr/bin/env python3

"""
//! \brief A script to fill in environment passwords local to your system
//! \version v1
//! \copyright Select Comfort Proprietary and Confidential
//! \copyright Copyright 2018, All Rights Reserved
"""

"""
A utility script to edit your local copy of the enviroment configuration file: config.json  


"""

import sys
import json
import logging
import os
import argparse
import datetime
import time
import shutil

VERSION = "0.1.0"
REPLACE_ME = "xxxxx"

def debugging(debug):
    if debug:  # log to screen
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S')
    else:
        logging.disable(logging.CRITICAL)

#
def Main():
    global fwrite, backendServer_UserName, backendServer_URL, backendServer_Password
    parser = argparse.ArgumentParser(description='CDC utility.')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug logging')
    parser.add_argument('--env', nargs='?', default="circle1", help='set the server environment, circle1 default [circle1, circle2, test, stage, ...]')
    parser.add_argument('--username', metavar='<username>',     type=str, required=False, help='backoffice username')
    parser.add_argument('--password', metavar='<password>',     type=str, required=False, help='backoffice password')
    parser.add_argument('--ssh_user', metavar='<ssh username>', type=str, required=False, help='ssh username for boson (depends on your ssh config)')
    parser.add_argument('--sql_user', metavar='<sql username>', type=str, required=False, help='sql username')
    parser.add_argument('--sql_pass', metavar='<sql password>', type=str, required=False, help='sql password')

    args = parser.parse_args()

    # setup debugging
    debugging(args.debug)

    # load server configurations
    CONFIG_JSON = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__), "config.json"))
    try:
        config = json.load(open(CONFIG_JSON))
    except Exception as err:
        print(err)
        print("ERROR: could not load config.json")
        sys.exit(-1)

    # create timestamp
    backup_filename = time.strftime("config_%Y%m%d%H%M%S.json")
    shutil.copy2(CONFIG_JSON, "{}_{}.txt".format(CONFIG_JSON, backup_filename))

    if config[args.env] == None:
        print("ERROR: {} environment does not exist".format(args.env))
        sys.exit(-1)

    if config[args.env]['backoffice']['username'] != REPLACE_ME:
        print("WARNING: replacing existing username")
    config[args.env]['backoffice']['username'] = args.username

    if config[args.env]['backoffice']['password'] != REPLACE_ME:
        print("WARNING: replacing existing password")
    config[args.env]['backoffice']['password'] = args.password

    if (args.sql_user != None):
        if config[args.env]['sql']['sql_username'] != REPLACE_ME:
            print("WARNING: replacing existing sql username")
        config[args.env]['sql']['sql_username'] = args.sql_user

    if (args.sql_pass != None):
        if config[args.env]['sql']['sql_password'] != REPLACE_ME:
            print("WARNING: replacing existing sql username")
        config[args.env]['sql']['sql_password'] = args.sql_pass

    if (args.ssh_user != None):
        if config[args.env]['sql']['ssh_username'] != REPLACE_ME:
            print("WARNING: replacing existing ssh username")
        config[args.env]['sql']['ssh_username'] = args.ssh_user

    # Now let's write out the new configuration file
    file = open(CONFIG_JSON, "w")
    file.write(json.dumps(config, indent=2, sort_keys=True))
    file.close()
    print("done")

if __name__ == '__main__':
    Main()
