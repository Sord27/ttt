#!/usr/bin/env python3

"""
Given a mac address, boson to the device and send the bamlog through a filter to extract all the
Pump2Algo and Pump2Serv logs and reformat the foundation data for importing into a spreadsheet. The logs
are sorted before printing first by Pump2Algo/Pump2Serv, then by side, then by time.
"""

import sys
import pexpect
import argparse

parser = argparse.ArgumentParser(description='test helper for BAM-7915')
parser.add_argument("macaddress",  help="The mac address of the device to operate upon")
parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
parser.add_argument("-q", "--quiet", action="store_true")
args = parser.parse_args()

bosonPrompt = "[#\$]"

def boson_login(macaddress):
    child = pexpect.spawn("ssh -t -t -p 6022 boson sessh -f %s" % (macaddress))
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

def get_parsed_device_log(macaddress):
    child = boson_login(macaddress)
    child.sendline("ls -l /var/log/bam*")
    child.expect(bosonPrompt)
    logdata = child.before.decode()
    child.sendline("cat /var/log/bamlog | grep Pump2Algo")
    child.expect(bosonPrompt)
    logdata = child.before.decode()
    sed = "sed -rn \"s/(.*) 500-([A-Fa-f0-9]{12}).*(Pump2Serv|Pump2Algo).*(0000000[01]).*f ([0-9]{2}) n.*fpos.h ([0-9]{3}) f ([0-9]{3}).*/\\2\\t\\3\\t\\4\\t\\1\\t\\5\\t\\6\\t\\7/p\""
    child.sendline("cat /var/log/bamlog | grep Pump2 | " + sed)
    child.expect(bosonPrompt)
    logdata = child.before.decode()
    child.sendline("exit")
    sorted_lines = sorted(logdata.splitlines(True))
    logdata = [x for x in sorted_lines if x.startswith(macaddress)]
    return(''.join(logdata))

def Main():
    x = get_parsed_device_log(args.macaddress.lower())
    print(x)

if __name__ == '__main__':
    Main()
