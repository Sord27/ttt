"""
//! \brief A script to reset 360 smart-pump using reset GPIO pin
    for given set of devices
//! \version v2 Multiprocessing version
Output file columns:
| Query MAC | Status |
"""

import time
import sys
import logging
import datetime
import json
import multiprocessing
import pexpect
from pexpect import pxssh


LOCK = ''

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
                "Got an exception, cannot login into boson, please check credentials")
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

    @classmethod
    def write_to_file(cls, mesg):
        """Write status to file"""
        write_to_file = open("out_boson", 'a+')
        LOCK.acquire()
        write_to_file.write(mesg)
        write_to_file.close()
        LOCK.release()



def debugging(debug, debug_to_file):
    """ Handle debugging/logging for this script """
    if debug_to_file:  # log to file
        logging.basicConfig(
            level=logging.DEBUG,
            format=
            '%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
            datefmt='%a, %d %b %Y %H:%M:%S',
            filename='boson_reset_sp360_mlp.log',
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
    command1 = "bamio -t -k PSNR"
    command2 = "echo 93 > /sys/class/gpio/export;"
    "echo out > /sys/class/gpio/gpio93/direction;sleep 2;"
    "echo 1 > /sys/class/gpio/gpio93/value;echo 93 > /sys/class/gpio/unexport"
    # Assumed each line contains mac only
    mac = line.lower().replace('\n', '')
    mac = mac.replace(' ', '')
    boson = BosonServer()
    boson.set_credentials()
    boson.check_credentials()
    boson_server_status = boson.establish_connection()
    if boson_server_status == False:
        logging.error("Unable to establish connection with boson, exiting..")
        BosonServer.write_to_file(mac + '\t exception1\n')
        return
    if boson_server_status == "EXCP":
        logging.error("An exception occurred while communicating with Boson server ")
        BosonServer.write_to_file(mac + '\t exception2\n')
        return

    # Get device connection from boson
    device = boson.get_device(mac)
    if device == "notinboson":
        print(mac + "\tNot found in boson")
        BosonServer.write_to_file(mac + '\tNot found in boson\n')
        return ("Not found in boson", mac)
    if device == "EOF":
        print(mac + "\tBoson EOF error")
        BosonServer.write_to_file(mac + '\tBoson EOF error\n')
        return ("Boson EOF error", mac)
    if device == "Timed-out":
        print(mac + "\tDevice connection timed out")
        BosonServer.write_to_file(mac + '\tDevice connection timed out\n')
        return ("Device connection timed out", mac)

    terminal = boson.get_instance()

    try:
        if device:
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
                    print(mac + '\tSP recovered')
                    BosonServer.write_to_file(mac + '\tSP recovered\n')
                    return ("SP recovered", mac)
                print(mac + '\tSP not recovered')
                BosonServer.write_to_file(mac + '\tSP not recovered\n')
                return ("SP not recovered", mac)

            else:
                print(mac + "\tSP is functional")
                BosonServer.write_to_file(mac + '\tSP is functional\n')
                return ("functional", mac)
            # Exit from device
            terminal.sendline("exit")
            terminal.expect("closed")

        else:
            print(mac + "\toffline")
            BosonServer.write_to_file(mac + '\toffline\n')
            return ("offline", mac)


    except pexpect.ExceptionPexpect as exc:
        logging.error("Exception for %s: %s", mac, exc)
        print(mac + ",exception")
        BosonServer.write_to_file(mac + '\t exception\n')


def usage():
    """ Show usage for this script """
    print("python3 boson_reset_sp360_mlp.py <input_file_name>")
    sys.exit(1)


def init(init_lock):
    """initiate global lock """
    global LOCK
    LOCK = init_lock


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

    init_lock = multiprocessing.Lock()
    pool = multiprocessing.Pool(initializer=init, initargs=(init_lock, ))
    pool.map(boson_reset_sp360, get_mac_list)
    pool.close()
    pool.join()
    endtime = datetime.datetime.now()
    print(endtime - starttime)
    sys.exit(0)


if __name__ == '__main__':
    main()
