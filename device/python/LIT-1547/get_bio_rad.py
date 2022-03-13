"""
//! \brief A script to extract bio rad result from pump(s)
    for given set of devices
//! \version v2
"""

import sys
import logging
import datetime
import json
import multiprocessing
import pexpect
from pexpect import pxssh


class BosonServer:
    """ Boson server credentials """
    prompt = '[#|$]'
    timeout = 10

    def __init__(self):
        """ Keep the compiler happy """
        self.url = None
        self.username = None
        self.port = None
        self.prompt = None
        self.timeout = None
        self.password = None
        self.ssh_key = None
        self.instance = None

    def set_credentials(self):
        """ Set boson server credentials from secret.json file """
        with open('secret.json') as json_file:
            data = json.load(json_file)
            self.url = data["boson_url"]
            self.username = data["boson_username"]
            self.port = data["boson_port"]
            self.prompt = BosonServer.prompt
            self.timeout = BosonServer.timeout
            self.password = data["boson_password"]
            self.ssh_key = data["boson_ssh_key"]

    def check_credentials(self):
        """ Check if given boson server credentials are valid """
        if self.username == "xxxxx" or self.password == "xxxxx" \
                or self.ssh_key == "xxxxx":
            print("Please enter valid boson credentials!")
            sys.exit(1)

    def establish_connection(self):
        """ Try getting boson SSH connection """
        try:
            ssh_instance = pxssh.pxssh()
            if ssh_instance.login(self.url,
                                  self.username,
                                  port=self.port,
                                  original_prompt=self.prompt,
                                  login_timeout=self.timeout,
                                  ssh_key=self.ssh_key):
                ssh_instance.sendline('uptime')
                test_server = ssh_instance.expect(['load'])

                if test_server == 0:
                    logging.debug(
                        "Connected to boson and ready to access devices:")
                    self.instance = ssh_instance
                else:
                    logging.debug(
                        "Connected to boson, but cannot access devices!")
                    return False

        except pexpect.ExceptionPexpect as exc:
            print(exc)
            logging.error(str(exc))
            logging.error(
                "Got an exception, cannot login into boson, please check credentials"
            )
            return "EXCP"

    def get_instance(self):
        """ Returns established boson SSH instance """
        return self.instance

    def get_device(self, mac):
        """
        Try getting terminal instance to specific device from boson server
        """
        expected1 = "ECDSA key fingerprint is "
        expected2 = "password:"
        expected3 = "No CSTAT entry found in NFS, looping."
        try:
            self.instance.sendline('bamssh ' + mac)
            expected = self.instance.expect([
                expected1, expected2, expected3, pexpect.EOF, pexpect.TIMEOUT
            ])

            if expected == 0:
                self.instance.sendline("yes")
                if self.instance.expect("password") == 0:
                    self.instance.sendline(self.password)
                if self.instance.expect("#") == 0:
                    logging.debug("Connected to %s", mac)
                    return True
            elif expected == 1:
                self.instance.sendline(self.password)
                if self.instance.expect("#") == 0:
                    logging.debug("Connected to %s", mac)
                    return True
            elif expected == 2:
                logging.error("Device not found, skip")
                return "notinboson"
            elif expected == 3:
                logging.error("Error device sent EOF")
                return "EOF"
            elif expected == 4:
                logging.error("Error device timed out")
                return "Timed-out"
            return False

        except pexpect.ExceptionPexpect as exc:
            logging.error("Exception in get_device(%s): %s", mac, exc)
            return False


def debugging(debug, debug_to_file):
    """ Handle debugging/logging for this script """
    if debug_to_file:  # log to file
        logging.basicConfig(
            level=logging.DEBUG,
            format=
            '%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
            datefmt='%a, %d %b %Y %H:%M:%S',
            filename='get_bio_rad.log',
            filemode='w')
    if debug is True:  # log to screen
        logging.basicConfig(
            level=logging.DEBUG,
            format=
            '%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
            datefmt='%a, %d %b %Y %H:%M:%S')
    else:
        logging.disable(logging.CRITICAL)


def boson_get_bio_rad(line):
    """ Get responsive air events logs through bio command """
    # Assumed each line contains mac only
    mac = line.lower().replace('\n', '')
    mac = mac.replace(' ', '')
    BOSON = BosonServer()
    BOSON.set_credentials()
    BOSON.check_credentials()
    boson_server_status = BOSON.establish_connection()
    if boson_server_status == False:
        logging.error("Unable to establish connection with boson, exiting..")
        return mac + '\t exception1\n'

    if boson_server_status == "EXCP":
        logging.error(
            "An Expection occured while communicating with Boson server ")
        return mac + '\t exception2\n'

    # Get device connection from boson
    device = BOSON.get_device(mac)
    if device == "notinboson":
        return mac + " Not found in Boson"
    if device == "EOF":
        return mac + "Boson EOF Error"
    if device == "Timed-out":
        return mac + "Device connection Timedout"

    terminal = BOSON.get_instance()

    try:
        if device:
            # Get RAD logs
            terminal.sendline("bio rad")
            terminal.expect("~#")
            print(mac + ",success")
            convert_to_string = (terminal.before).decode("utf-8")
            # Exit from device
            terminal.sendline("exit")
            terminal.expect("closed")
            return mac + '\n' + convert_to_string + '\n'
        print(mac + "\toffline")
        return mac + "\toffline\n"

    except pexpect.ExceptionPexpect as exc:
        logging.error("Exception for %s: %s", mac, exc)
        print(mac + ",exception")
        return mac + "\texception\n"


def usage():
    """ Show usage for this script """
    print("python3 get_bio_rad.py <input_file_name>")
    sys.exit(1)


def main():
    """ Main entry point for this script """

    debugging(False, False)

    if len(sys.argv) != 2:
        usage()

    input_filename = sys.argv[1]
    fread = open(input_filename, 'r')
    starttime = datetime.datetime.now()
    get_mac_list = []
    for line in fread:
        get_mac_list.append(line)

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    results = pool.map(boson_get_bio_rad, get_mac_list)

    timestamp = datetime.datetime.now().strftime("%y%m%d%H%M")
    output_filename = "out_get_bio_rad_" + timestamp + ".txt"
    fwrite = open(output_filename, 'w')
    for x in results:
        fwrite.write(str(x))
        fwrite.write(
            "\n------------------------------------------------------------------\n\n"
        )

    pool.close()
    pool.join()
    endtime = datetime.datetime.now()
    time_to_complete = str(endtime - starttime)
    print("Time to complete: " + time_to_complete)
    fwrite.write("Time to complete: " + time_to_complete)
    fwrite.close()
    sys.exit(0)


if __name__ == '__main__':
    main()
