"""
//! \brief A script to reset 360 smart-pump using reset GPIO pin
    for given set of devices
//! \version v1

Output file columns:
| Query MAC | Status |
"""

import datetime
import time
import os
import sys
import threading
import json
import logging
from multiprocessing.dummy import Pool as ThreadPool
import requests
from requests.auth import HTTPBasicAuth

UNIX_COMMAND = ''
FWRITE = ''
LOCK = ''
SERVER = ''


class BackendServer:
    """ Backend server credentials """
    url = 'xxxxx'
    username = 'xxxxx'
    password = 'xxxxx'

    def set_backend_credentials(self):
        """ Set backend server credentials from secret.json file """
        with open('secret.json') as json_file:
            data = json.load(json_file)
            self.url = data["backend_url"]
            self.username = data["backend_username"]
            self.password = data["backend_password"]

    def check_credentials(self):
        """ Check if given backend server credentials are valid """
        if self.url == "xxxxx" or self.username == "xxxxx" \
                or self.password == "xxxxx":
            print("Please enter valid backend credentials!")
            sys.exit(0)

    def get_cdc_key(self, mac, key):
        """ Getter request for given device and BAMkey """
        cdc_key = [{"macAddress": mac, "cdcKey": key}]
        headers = {'content-type': 'application/json'}
        test = requests.put(self.url + 'getCdcValues',
                            auth=HTTPBasicAuth(self.username, self.password),
                            headers=headers,
                            data=json.dumps(cdc_key))
        data = json.loads(test.text)

        if data[0]['success']:
            if data[0]['value'] == "":
                if data[0]['failureReason'] is None:
                    logging.error("%s:%s:OFFLINE empty return", mac, key)
                else:
                    logging.error(mac + ":" + key + ":OFFLINE " +
                                  str(data[0]['failureReason']))
            else:
                logging.debug(mac + ":" + key + ":" + data[0]['value'] + '\n')
                return data[0]['value']
        else:
            logging.error("%s:%s:OFFLINE %s", mac, key,
                          data[0]['failureReason'])
        return None

    def set_cdc_key(self, mac, key, value):
        """ Setter request for given device and BAMkey """
        cdc_key = [{"macAddress": mac, "cdcKey": key, "value": value}]
        headers = {'content-type': 'application/json'}
        test = requests.put(self.url + 'setCdcValues',
                            auth=HTTPBasicAuth(self.username, self.password),
                            headers=headers,
                            data=json.dumps(cdc_key))
        data = json.loads(test.text)

        if data[0]['success']:
            logging.debug(mac + ":" + key + ":" + data[0]['value'])
            return True
        logging.error(mac + ":" + key + ":" + str(value) + ":OFFLINE")
        return False

    def send_rpc_command(self, mac, command):
        """ Send RPC command for given device """
        request_body = {"macAddress": mac, "unixCommand": command}
        headers = {'content-type': 'application/json'}
        test = requests.post(self.url + 'deviceRPC',
                             auth=HTTPBasicAuth(self.username, self.password),
                             headers=headers,
                             data=json.dumps(request_body))
        data = json.loads(test.text)
        logging.debug(data)


def debugging(debug, debug_to_file):
    """ Handle debugging/logging for this script """
    if debug_to_file:  # log to file
        logging.basicConfig(
            level=logging.DEBUG,
            format=
            '%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
            datefmt='%a, %d %b %Y %H:%M:%S',
            filename='backend_reset_sp360.log',
            filemode='w')
    if debug:  # log to screen
        logging.basicConfig(
            level=logging.DEBUG,
            format=
            '%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
            datefmt='%a, %d %b %Y %H:%M:%S')
    else:
        logging.disable(logging.CRITICAL)


def load_rpc_command():
    """ Load RPC command from command.json file """
    global UNIX_COMMAND
    with open('command.json') as json_file:
        data = json.load(json_file)
        UNIX_COMMAND = data["unix_command"]
    logging.debug(UNIX_COMMAND)


def backend_reset_sp360(line):
    """ Reset 360 smart-pump if it's stuck and log status in the file """
    global FWRITE, UNIX_COMMAND, LOCK
    # Assumed each line contains MAC only
    line = line.split('\t')
    line = line[0]
    mac = line.upper().replace('\n', '')
    mac = mac.replace(' ', '')

    # Get Bammit application version
    value = SERVER.get_cdc_key(mac, "SAPP")
    if value is None:
        status = "offline"
    # Device is online
    else:
        # Get User SN
        value = SERVER.get_cdc_key(mac, "PSNR")
        # Smart-pump is stuck
        if value is None:
            # Send RPC command to reset smart-pump K20 controller
            SERVER.send_rpc_command(mac, UNIX_COMMAND)
            time.sleep(10)
            # Get User SN
            value = SERVER.get_cdc_key(mac, "PSNR")
            if value is None:
                status = "SP not recovered"
            else:
                status = "SP recovered"
        # SP has been functional so no need of SP reset
        else:
            status = "SP is functional"

    print(mac + "," + status)
    LOCK.acquire()
    try:
        FWRITE.write(mac + "\t" + status + "\n")
    finally:
        LOCK.release()


def usage():
    """ Show usage for this script """
    print("python3 backend_reset_sp360.py <input_file_name>")
    sys.exit(0)


def main():
    """ Main entry point for this script """
    global FWRITE, SERVER, LOCK
    debug = False  # Enable logging to the console
    debug_to_file = False  # Enable logging to the file
    debugging(debug, debug_to_file)
    SERVER = BackendServer()
    if len(sys.argv) == 2:
        SERVER.set_backend_credentials()
        SERVER.check_credentials()
        input_filename = sys.argv[1]
        if os.path.isfile(input_filename):
            fread = open(input_filename, 'r')
            timestamp = datetime.datetime.now().strftime("%y%m%d%H%M")
            output_filename = "out_backend_reset_sp360_" + timestamp + ".txt"
            FWRITE = open(output_filename, 'w')
            lines = fread.readlines()
            load_rpc_command()

            # Create a lock object
            LOCK = threading.Lock()

            # Make the Pool of workers
            pool = ThreadPool(8)  # CHANGE ME if needed
            pool.map(backend_reset_sp360, lines)

            # close the pool and wait for the work to finish
            pool.close()
            pool.join()
            FWRITE.close()
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
    main()
