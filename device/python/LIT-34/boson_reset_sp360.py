"""
//! \brief A script to reset 360 smart-pump using reset GPIO pin
    for given set of devices
//! \version v1

Output file columns:
| Query MAC | Status |
"""

import time
import sys
import logging
import datetime
import json
import pexpect
from pexpect import pxssh

FWRITE = ''
BOSON = ''


class BosonServer:
    """ Boson server credentials """
    url = 'devices.dev.siq.sleepnumber.com'
    port = '6022'
    prompt = '[#|$]'
    timeout = 10
    username = "xxxxx"
    password = "xxxxx"
    ssh_key = "xxxxx"
    instance = None

    def set_credentials(self):
        """ Set boson server credentials from secret.json file """
        with open('secret.json') as json_file:
            data = json.load(json_file)
            self.username = data["boson_username"]
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

        except pexpect.ExceptionPexpect as exc:
            logging.error(str(exc))
            logging.error("Got an exception, cannot login into "
                          "boson, please check credentials")

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
                logging.error("Device not found, sending ctrl+c")
                self.instance.sendcontrol("C")
            elif expected == 3:
                logging.error("Error device sent EOF")
            elif expected == 4:
                logging.error("Error device timed out")
                self.instance.sendcontrol("C")
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
            filename='boson_reset_sp360.log',
            filemode='w')
    if debug is True:  # log to screen
        logging.basicConfig(
            level=logging.DEBUG,
            format=
            '%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
            datefmt='%a, %d %b %Y %H:%M:%S')
    else:
        logging.disable(logging.CRITICAL)


def boson_reset_sp360(line):
    """ Reset 360 smart-pump if it's stuck and log status in the file """
    global FWRITE, BOSON
    command1 = "bamio -t -k PSNR"
    command2 = "echo 93 > /sys/class/gpio/export;"
    "echo out > /sys/class/gpio/gpio93/direction;sleep 2;"
    "echo 1 > /sys/class/gpio/gpio93/value;echo 93 > /sys/class/gpio/unexport"
    # Assumed each line contains mac only
    mac = line.lower().replace('\n', '')
    mac = mac.replace(' ', '')

    # Get device connection from boson
    device = BOSON.get_device(mac)
    terminal = BOSON.get_instance()

    try:
        if device == 0:
            # Check User SN
            terminal.sendline(command1)
            terminal.readline()
            output = terminal.readline().decode('utf-8').strip("\r\n")
            terminal.expect("~#")
            if not output.isdigit():
                # Reset smart-pump
                terminal.sendline(command2)
                terminal.expect("~#")
                # Keep on pinging every 5 seconds to check if SP is alive
                for _ in range(0, 5):
                    time.sleep(5)
                    # Check User SN
                    terminal.sendline(command1)
                    terminal.readline()
                    output = terminal.readline().decode('utf-8').strip("\r\n")
                    terminal.expect("~#")
                    if output.isdigit():
                        break
                if output.isdigit():
                    print(mac + ",SP recovered")
                    FWRITE.write(mac + '\tSP recovered\n')
                else:
                    print(mac + ",SP not recovered")
                    FWRITE.write(mac + '\tSP not recovered\n')
            else:
                print(mac + ",SP is functional")
                FWRITE.write(mac + '\tSP is functional\n')

            # Exit from device
            terminal.sendline("exit")
            terminal.expect("closed")

        else:
            print(mac + ",offline")
            FWRITE.write(mac + '\toffline\n')
    except pexpect.ExceptionPexpect as exc:
        logging.error("Exception for %s: %s", mac, exc)
        print(mac + ",exception")
        FWRITE.write(mac + '\texception\n')


def usage():
    """ Show usage for this script """
    print("python3 boson_reset_sp360.py <input_file_name>")
    sys.exit(1)


def main():
    """ Main entry point for this script """
    global FWRITE, BOSON

    debugging(False, False)

    if len(sys.argv) != 2:
        usage()

    input_filename = sys.argv[1]
    fread = open(input_filename, 'r')
    timestamp = datetime.datetime.now().strftime("%y%m%d%H%M")
    output_filename = "out_boson_reset_sp360_" + timestamp + ".txt"
    FWRITE = open(output_filename, 'w')

    BOSON = BosonServer()
    BOSON.set_credentials()
    BOSON.check_credentials()
    BOSON.establish_connection()
    if BOSON.get_instance() is None:
        logging.error("Unable to establish connection with boson, exiting..")
        sys.exit(1)

    for line in fread:
        boson_reset_sp360(line)

    # Exit from boson
    BOSON.get_instance().sendline("exit")
    BOSON.get_instance().terminate()
    FWRITE.close()
    fread.close()
    sys.exit(0)


if __name__ == '__main__':
    main()
