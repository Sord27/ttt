#!/usr/bin/env python

"""
//! \brief A script to execute a terminal command on the device over boson.
//! \version v1
//! \copyright Sleep Number Proprietary and Confidential
//! \copyright Protected by Copyright 2017-2018
"""

import pexpect
from pexpect import pxssh
import sys
import logging

# Boson Parameters
bosonServer = 'devices.dev.siq.sleepnumber.com'
bosonUser = 'dhruv'             # CHANGE ME
bosonPort = '6022'
bosonPrompt = '[#|$]'
bosonTimeout = 10
bosonSSHKEY = '~/.ssh/id_rsa'   # CHANGE ME

# Debugging
debug = False
debugToFile = False


def debugging(debug, debugToFile):
    if debug is True and debugToFile is True:  # log to file
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filename='exec_boson_cmd.log',
                            filemode='w')
    if debug is True:  # log to screen
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S')
    else:
        logging.disable(logging.CRITICAL)


def get_boson():
    try:
        s = pxssh.pxssh()
        i = s.login(bosonServer, bosonUser, port=bosonPort,
                    original_prompt=bosonPrompt, login_timeout=bosonTimeout,
                    ssh_key=bosonSSHKEY)

        if i is True:
            s.sendline('uptime')
            test_server = s.expect(['load'])
            if test_server == 0:
                print("Connected to boson and ready to access devices:")
                return s
            else:
                print('Connected to boson, but cannot access devices!')
                return None

    except pexpect.ExceptionPexpect as e:
        logging.debug(e)
        logging.debug("An exception error had occured, cannot login into " +
                      "boson, please check credintial, network or private key")
        return None


def get_device(boson, MAC):
    testcase1 = "ECDSA key fingerprint is "
    testcase2 = "password:"
    testcase3 = "No CSTAT entry found in NFS, looping."
    try:
        boson.sendline('bamssh ' + MAC)
        testcase = boson.expect([testcase1, testcase2, testcase3, pexpect.EOF,
                                pexpect.TIMEOUT])
        if testcase == 0:
            boson.sendline("yes")
            if boson.expect("password") == 0:
                boson.sendline("bam!ssh")
            if boson.expect("#") == 0:
                print("Connected to " + MAC)
                return 0
        elif testcase == 1:
            boson.sendline("bam!ssh")
            if boson.expect("#") == 0:
                print("Connected to " + MAC)
                return 0
        elif testcase == 2:
            print("Device not found, sending ctrl+c")
            boson.sendcontrol("C")
            return 3
        elif testcase == 3:
            print("Error device sent EOF")
            return 4
        elif testcase == 4:
            print("Error device timed out")
            return 5
        else:
            return -1

    except pexpect.ExceptionPexpect as e:
        print("Exception in get_device(" + MAC + "): " + e)
        return 6


def usage():
    print("python exec_boson_cmd.py <Mac> <terminal_command>")
    print("e.g. python exec_boson_cmd.py 64dba0000144 'bio system'")
    sys.exit()


def Main():
    debugging(debug, debugToFile)

    if len(sys.argv) != 3:
        usage()

    MAC = sys.argv[1]
    command = sys.argv[2]

    # Get boson connection
    boson = get_boson()
    if boson is None:
        print("Unable to establish connection with boson, exiting..")
        sys.exit()

    # Get device connection from boson
    device = get_device(boson, MAC)
    if device == 0:
        boson.sendline(command)
        boson.expect("root@500-" + MAC.lower() + ":~#")
        print(boson.before.decode())

        # Exit from device
        boson.sendline("exit")
        boson.expect("$")

        # Exit from boson
        boson.sendline("exit")
        boson.kill(0)
        sys.exit()
    else:
        print("Not able to connect with " + MAC)


if __name__ == '__main__':
    Main()
