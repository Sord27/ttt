#!/usr/bin/env python

"""
//! \brief A script to blow fuses for given devices over boson
//! \version v2
"""

import pexpect
from pexpect import pxssh
import sys
import logging
import datetime

# Boson Parameters
bosonServer = 'devices.dev.siq.sleepnumber.com'
bosonUser = 'CHANGE_ME'                                 # CHANGE_ME
bosonPort = '6022'
bosonPrompt = '[#|$]'
bosonTimeout = 10
bosonSSHKEY = "CHANGE_ME/.ssh/id_rsa"                   # CHANGE_ME

# Debugging
debug = False
debugToFile = False


def debugging(debug, debugToFile):
    if debug is True and debugToFile is True:  # log to file
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filename='blow_fuses_360.log',
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
                logging.debug("Connected to boson and ready to access devices:")
                return s
            else:
                logging.debug('Connected to boson, but cannot access devices!')
                return None

    except pexpect.ExceptionPexpect as e:
        logging.error(e)
        logging.error("An exception error had occured, cannot login into " +
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
                logging.debug("Connected to " + MAC)
                return 0
        elif testcase == 1:
            boson.sendline("bam!ssh")
            if boson.expect("#") == 0:
                logging.debug("Connected to " + MAC)
                return 0
        elif testcase == 2:
            logging.error("Device not found, sending ctrl+c")
            boson.sendcontrol("C")
            return 3
        elif testcase == 3:
            logging.error("Error device sent EOF")
            return 4
        elif testcase == 4:
            logging.error("Error device timed out")
            boson.sendcontrol("C")
            return 5
        else:
            return -1

    except pexpect.ExceptionPexpect as e:
        logging.error("Exception in get_device(" + MAC + "): " + e)
        return 6


def usage():
    print("python blow_fuses_360.py <filename>")
    print("e.g. python blow_fuses_360.py deviceList.txt")
    sys.exit()


def Main():
    debugging(debug, debugToFile)

    if len(sys.argv) != 2:
        usage()

    input_filename = sys.argv[1]
    fread = open(input_filename, 'r')
    timestamp = datetime.datetime.now().strftime("%y%m%d%H%M")
    output_filename = "out_blow_fuses_360_" + timestamp + ".txt"
    fwrite = open(output_filename, 'w')
    command1 = "echo 0x4060 > /sys/fsl_otp/HW_OCOTP_CFG4"
    command2 = "echo 0x00200010 > /sys/fsl_otp/HW_OCOTP_CFG5"

    # Get boson connection
    boson = get_boson()
    if boson is None:
        logging.error("Unable to establish connection with boson, exiting..")
        sys.exit()

    for line in fread:
        MAC = line.lower().replace('\n','')            # Assumed each line contains MAC only
        MAC = MAC.replace(' ','')

        # Get device connection from boson
        device = get_device(boson, MAC)

        try:
            if device == 0:
                # Light the fuse
                boson.sendline(command1)
                boson.expect("~#")
                boson.sendline(command2)
                boson.expect("~#")

                print(MAC + ",success")
                fwrite.write(MAC + '\tsuccess\n')

                # Exit from device
                boson.sendline("exit")
                boson.expect("closed")

            else:
                print(MAC + ",offline")
                fwrite.write(MAC + '\toffline\n')
        except pexpect.ExceptionPexpect as e:
            logging.error("Exception in blowing fuses for " + MAC + ": " + e)
            print(MAC + ",exception")
            fwrite.write(MAC + '\texception\n')

    # Exit from boson
    boson.sendline("exit")
    boson.terminate()
    fwrite.close()
    fread.close()
    sys.exit()


if __name__ == '__main__':
    Main()
