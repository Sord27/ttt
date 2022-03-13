
from argparse import ArgumentParser
from csv import DictReader
import os
import subprocess
from time import time
import log


MAX_MACS_COUNT = 32
MAX_BOSON_INDEX = 150


if __name__ == "__main__":
    argparser = ArgumentParser(description="execute specified script on boson for devices listed in CSV file remotely")

    argparser.add_argument("script_file", type=str,
                           help="script file to upload to boson and execute")

    argparser.add_argument("csv_file", type=str,
                           help=".csv file to read the list of devices from")

    argparser.add_argument("-n", "--boson-n", type=int, default=1,
                           help="boson server index to use")

    args = argparser.parse_args()
    macs_ht = {}

    if not os.path.isfile(args.script_file):
        log.fatal("Unable to access script file [{}]".format(args.script_file))

    if not os.path.isfile(args.csv_file):
        log.fatal("Unable to access macs list file [{}]".format(args.csv_file))
    
    macs_file = open(args.csv_file, 'r')
    macs_file_lines = macs_file.readlines()

    macs_count = 0
    macs_file_lines.pop(0)
    macs_single_line = ""
    
    for mac in macs_file_lines:
        macs_count += 1
        try:
            int(mac, base=16)
        except ValueError:
            log.fatal("corrupted mac (`{}')".format(mac))
        macs_single_line += mac[0:12]
        macs_single_line += " "
 
    log.info("Found {} macs in [{}] list file: {}".format(macs_count, args.csv_file, macs_single_line))

    if args.boson_n > MAX_BOSON_INDEX:
        log.fatal("invalid boson server index")

    boson = "boson-boson{}".format(args.boson_n)

    # Provision the script

    try:
        log.info("provisioning {} with {} script".format(boson, args.script_file))
        subprocess.run("scp {} {}:~".format(args.script_file, boson),
                       shell=True, check=True)

        cmd = "ssh {} ' ./{} {}'"
        cmd = cmd.format(boson, os.path.basename(args.script_file), macs_single_line)
        log.info("running {} script".format(os.path.basename(args.script_file)))
        subprocess.run(cmd, shell=True, check=True)

        cmd = "ssh {} 'rm {}'".format(boson, os.path.basename(args.script_file))

        log.info("cleaning up")
        subprocess.run(cmd, shell=True, check=True)

        log.info("Done!")
    except subprocess.CalledProcessError as e:
        log.info(e)
        log.fatal("One of the SSH calls failed.")
