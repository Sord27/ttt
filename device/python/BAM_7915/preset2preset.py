#!/usr/bin/env python3

"""
"""

import sys
import time
import json, requests
from requests.auth import HTTPBasicAuth
import logging
import datetime
import pexpect
import argparse

parser = argparse.ArgumentParser(description='test helper for BAM-7915')
parser.add_argument("macaddress",  help="The mac address of the device to operate upon")
parser.add_argument('--environment', help='Server environment device is connected to')
parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
parser.add_argument("-q", "--quiet", action="store_true")
parser.add_argument("--slow", help="articulate speed slow, default is fast", action="store_true")
parser.add_argument("--left", help="articulate left side", action="store_true")
parser.add_argument("--right", help="articulate right side", action="store_true")
parser.add_argument("--start", help="starting preset (custom,reading,tv,flat,zerog,snore) or (1-6)")
parser.add_argument("--end", help="finishing preset (custom,reading,tv,flat,zerog,snore) or (1-6)")
args = parser.parse_args()
if not args.environment:
    args.environment = "circle1"
print("ENVIRONMENT = %s" % args.environment)
env = json.load(open('config.json'))[args.environment]

backendServer_URL      = env['admin-svc']
backendServer_UserName = env['backoffice']['username']
backendServer_Password = env['backoffice']['password']
bosonPrompt = "[#\$]"

# speed
FAST = "0"
SLOW = "1"

if args.slow:
    SPEED=SLOW
else:
    SPEED=FAST

if args.left == False and args.right == False:
    print("You must select either --left or --right")
    sys.exit(-1)
    
# P=preset<1=Custom, 2=Reading, 3=Watch TV, 4=Flat, 5=Zero-G, 6=Snore>; S=speed<0-fast, 1-slow>
# if we don't match, set to flat (4)
def preset2str(preset):
    switcher = {
        "custom" : "1",
        "reading" : "2",
        "tv" : "3",
        "flat" : "4",
        "zerog" : "5",
        "snore" : "6"
    }
    if isinstance(preset,str) and len(preset) > 1:
        # assume a length of one that this is a single digit string indicating correct preset number
        preset_lower = str(preset).lower()
        return switcher.get(preset_lower, "4")
    elif isinstance(preset, int):
        return("%d" % args.end)
    else:
        return "4"

if args.start:
    preset = args.start
    args.start = preset2str(preset)
    print("specified start preset of %s : %s" % (preset, args.start))

if args.end:
    preset = args.end
    args.end = preset2str(preset)
    print("specified start preset of %s : %s" % (preset, args.end))

def getCdcKey(macaddress, key):
    global backendServer_URL, backendServer_UserName, backendServer_Password
    macaddress = macaddress.upper().replace('\n', '')
    macaddress = macaddress.replace(' ', '')
    if (',' in macaddress):
        macaddress = macaddress.split(',')[0]
    cdcKey = [{"macAddress": macaddress, "cdcKey": key}]
    headers = {'content-type': 'application/json'}
    try:
        test = requests.put(backendServer_URL + '/getCdcValues',
                            auth=HTTPBasicAuth(backendServer_UserName, backendServer_Password),
                            headers=headers,
                            data=json.dumps(cdcKey))
        notes = response = test.text
    except requests.ConnectionError as e:
        response = {"notes": "CONNECTIONERROR:" + str(e)}
        return response
    except requests.Timeout as e:
        response = {"notes": "TIMEOUT:" + str(e)}
        return response
    except requests.HTTPError as e:
        response = {"notes": "HTTPERROR:" + str(e)}
        return response
    except requests.exceptions.RequestException as e:
        response = {"notes": "ERROR:" + str(e)}
        return response

    data = ""
    try:
        data = json.loads(response)
    except ValueError:
        notes = test.text
    else:
        try:
            if data[0]['success']:
                pump_version = data[0]['value']
                notes = json.dumps(data, separators=(',', ':'))
            else:
                notes = response
        except:
            notes = json.dumps(data, separators=(',', ':'))
    finally:
        return data

def setCdcKey(MAC, key, value):
    global backendServer_URL, backendServer_UserName, backendServer_Password
    cdcKey = [{"macAddress": MAC, "cdcKey": key, "value": value}]
    headers = {'content-type': 'application/json'}
    url = backendServer_URL + '/setCdcValues'
    #print(json.dumps(cdcKey, indent=4, sort_keys=True))
    try:
        test = requests.put(url, auth=HTTPBasicAuth(backendServer_UserName, backendServer_Password), headers=headers, data=json.dumps(cdcKey))
        response = test.text
    except requests.ConnectionError as e:
        response = {"notes": "CONNECTIONERROR:" + str(e)}
        return response
    except requests.Timeout as e:
        response = {"notes": "TIMEOUT:" + str(e)}
        return response
    except requests.HTTPError as e:
        response = {"notes": "HTTPERROR:" + str(e)}
        return response
    except requests.exceptions.RequestException as e:
        response = {"notes": "ERROR:" + str(e)}
        return response


    # parse the response, should be valid JSON
    try:
        data = json.loads(test.text)
    except ValueError:
        print("Error parsing JSON response: " + test.text)
        return({})

    # check for server error code
    if test.status_code < 200 or test.status_code >= 300:
        print("SERVER ERROR")
        print(json.dumps(data, indent=4, sort_keys=True))
        return ({})

    if data[0] and data[0]['success']:
        print(key + ":" + data[0]['value'])
    else:
        print(key + ":FAILURE")
    # print(json.dumps(data, indent=4, sort_keys=True))
    return data

def usage():
    print()


def boson_login(macaddress):
    child = pexpect.spawn("ssh -t -t -p 6022 jonathancrockett@boson sessh -f %s" % macaddress)
    found = child.expect([pexpect.TIMEOUT, 'connecting \(yes\/no\)\?', 'password:'])
    if found == 0:
        print("ERROR TIMEOUT connecting to BOSON")
        sys.exit(-1)
    if found == 1: # yes/no prompt
        child.sendline('yes')
        child.expect("password:")
        child.sendline("bam!ssh")
    if found == 2: # skipped yes/no went right to password:
        child.sendline("bam!ssh")
    child.expect(bosonPrompt)
    return child

#
# clear current bamlog by forcing a logrotate so logging history is preserved
#
def clear_device_log(macaddress):
    child = boson_login(macaddress)
    child.sendline("logrotate -f /etc/logrotate.conf")
    child.expect(bosonPrompt)
    print(child.before.decode())
    child.sendline("exit")
    if child.isalive():
        child.close()

def get_device_log(macaddress):
    child = boson_login(macaddress)
    print("=====================================")
    child.sendline("cat /var/log/bamlog")
    child.expect(bosonPrompt)
    print(child.before.decode())
    print("=====================================")
    child.sendline("exit")

def get_parsed_device_log(macaddress):
    child = boson_login(macaddress)
    sed = "sed -rn \"s/(.*) 500-([A-Fa-f0-9]{12}).*(Pump2Serv|Pump2Algo).*(0000000[01]).*f ([0-9]{2}) n.*fpos.h ([0-9]{3}) f ([0-9]{3}).*/\\2\\t\\3\\t\\4\\t\\1\\t\\5\\t\\6\\t\\7/p\""
    child.sendline("cat /var/log/bamlog | grep Pump2 | " + sed)
    child.expect(bosonPrompt)
    logdata = child.before.decode()
    child.sendline("exit")
    sorted_lines = sorted(logdata.splitlines(True))
    logdata = [x for x in sorted_lines if x.startswith(macaddress)]
    return(''.join(logdata))

def Main():
    macaddress = args.macaddress.lower()

    # get foundation status
    # 400F0F000000000000000000000066
    print()
    print(getCdcKey(macaddress, "MFST"))
    print()

    clear_device_log(macaddress)

    print("Moving Foundation to starting position")
    print("")
    if args.left:
        x = setCdcKey(macaddress, "MFPL", args.start+SPEED)
        # print(json.dumps(x, indent=4, sort_keys=True))
        print(json.dumps(x))
    if args.right:
        x = setCdcKey(macaddress, "MFPR", args.start+SPEED)
        # print(json.dumps(x, indent=4, sort_keys=True))
        print(json.dumps(x))

    time.sleep(20)
    print("")

    print("")
    print(getCdcKey(macaddress, "MFST"))
    print("")

    print("Moving foundation to ending position")
    if args.left:
        x = setCdcKey(macaddress, "MFPL", args.end + SPEED)
        # print(json.dumps(x, indent=4, sort_keys=True))
        print(json.dumps(x))
    if args.right:
        x = setCdcKey(macaddress, "MFPR", args.end + SPEED)
        # print(json.dumps(x, indent=4, sort_keys=True))
        print(json.dumps(x))
    time.sleep(20)
    print("")
    print("")
    print(getCdcKey(macaddress, "MFST"))
    print("")

    print("")
    print("%s to %s" % (args.start, args.end))
    print("")
    output = get_parsed_device_log(macaddress)
    print(output)
    # f = open("output.tsv", 'w')
    # f.write(output)
    # f.close()

if __name__ == '__main__':
    Main()
