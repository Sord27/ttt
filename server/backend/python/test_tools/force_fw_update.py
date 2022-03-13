"""
//! \brief A script to force sleep-expert to upload firmwares from SE to SP
    for given set of devices
//! \version v1

Output file columns:
| Query MAC | Status |
"""

import datetime
import os
import sys
import threading
import json
import logging
from multiprocessing.dummy import Pool as ThreadPool
import requests

UNIX_COMMAND = ''
FWRITE = ''
LOCK = ''
SERVER = ''


class BackendServer:
    """ Backend server credentials """
    url = 'xxxxx'
    username = 'xxxxx'
    password = 'xxxxx'
    access_token = 'xxxxx'

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
        headers = {'content-type': 'application/json'}
        credential = {"login": self.username, "password": self.password}
        try:
            test = requests.put(self.url + 'authenticate?details=true',
                                headers=headers,
                                data=json.dumps(credential))
            test = json.loads(test.text)
            self.access_token = test["access_token"]
        except Exception as e:
            print("Failed to get access_token: ", str(e))

    def get_cdc_key(self, mac, key):
        """ Getter request for given device and BAMkey """
        cdc_key = [{"macAddress": mac, "cdcKey": key}]
        headers = {'content-type': 'application/json'}
        test = requests.put(self.url + 'getCdcValues?access_token=' +
                            self.access_token,
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
        test = requests.put(self.url + 'setCdcValues?access_token=' +
                            self.access_token,
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
        test = requests.post(self.url + 'deviceRPC?access_token=' +
                             self.access_token,
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
            filename='force_fw_update.log',
            filemode='w')
    if debug:  # log to screen
        logging.basicConfig(
            level=logging.DEBUG,
            format=
            '%(asctime)s %(levelname)-8s %(filename)s %(funcName)s(): %(lineno)d:\t %(message)s',
            datefmt='%a, %d %b %Y %H:%M:%S')
    else:
        logging.disable(logging.CRITICAL)


def force_fw_update(line):
    """ Force SE to update firmware on SP and log status in the file """
    global FWRITE, LOCK
    # Assumed each line contains MAC only
    line = line.split('\t')
    line = line[0]
    mac = line.upper().replace('\n', '')
    mac = mac.replace(' ', '')

    if mac == "":
        return

    # Get Bammit application version
    value = SERVER.get_cdc_key(mac, "SAPP")
    if value is None:
        status = "offline"
    # Device is online
    else:
        # Send RPC command to force firmware update
        SERVER.send_rpc_command(mac, "bio PFWD -1 -1 && sleep 1 && bio MFWU &")
        status = "success"

    print(mac + "," + status)
    LOCK.acquire()
    try:
        FWRITE.write(mac + "\t" + status + "\n")
    finally:
        LOCK.release()


def usage():
    """ Show usage for this script """
    print("python3 force_fw_update.py <input_file_name>")
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
            output_filename = "out_force_fw_update_" + timestamp + ".txt"
            FWRITE = open(output_filename, 'w')
            lines = fread.readlines()

            # Create a lock object
            LOCK = threading.Lock()

            # Make the Pool of workers
            pool = ThreadPool(8)  # CHANGE ME if needed
            pool.map(force_fw_update, lines)

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
