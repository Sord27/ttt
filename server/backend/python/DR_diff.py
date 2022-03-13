#!/usr/bin/env python

"""
//! \brief A script to get diff(additional new and not which lost) between
            2 Device Registry files.
//! \version v1
"""

import sys
import datetime
import os


def usage():
    print("python DR_diff.py <old_DR_file_name> <new_DR_file_name>")
    sys.exit(0)


def sort_files(files):
    out_files = []
    for file in files:
        output_file = "out_" + str(file)
        command = "sort " + file + " -o " + output_file
        os.system(command)
        out_files.insert(0, output_file)
    return out_files


def snip_files(files):
    out_files = []
    for file in files:
        snip_file = "snip_" + file
        fread = open(file, 'r')
        fwrite = open(snip_file, 'w')
        # Filter out 360 MAC only
        for line in fread:
            line = line.split('\t')
            MAC = line[0]
            MAC = MAC.upper().replace('\n', '')
            MAC = MAC.replace(' ', '')
            if MAC[:5] == "64DBA":
                fwrite.write(MAC + '\n')
            else:
                break
        fread.close()
        fwrite.close()
        out_files.insert(0, snip_file)
    return out_files


def get_new_additions(files):
    timestamp = datetime.datetime.now().strftime("%y%m%d%H%M")
    tmp_file = "tmp_" + timestamp + ".txt"

    # Take diff
    command = "diff " + files[0] + " " + files[1] + " > " + tmp_file
    os.system(command)

    # Filter out just new additions(not removals)
    diff_file = "out_DR_diff_" + timestamp + ".txt"
    fread = open(tmp_file, 'r')
    fwrite = open(diff_file, 'w')
    for line in fread:
        # Check for additions
        if line[:7] == "> 64DBA":
            fwrite.write(line[2:14] + '\n')
    fread.close()
    fwrite.close()
    return [tmp_file, diff_file]


def do_cleanup(files):
    for file in files:
        command = "rm " + file
        os.system(command)


def Main():
    if len(sys.argv) == 3:
        file1 = sys.argv[1]
        file2 = sys.argv[2]
        if os.path.isfile(file1) and os.path.isfile(file2):
            if file1 < file2:
                sorted_files = sort_files([file1, file2])
                snipped_files = snip_files(sorted_files)
                tmp_file, diff_file = get_new_additions(snipped_files)
                do_cleanup(sorted_files + snipped_files + [tmp_file])
            else:
                print("Input file order doesn't look correct!")
                print("Please keep timestamp there with filename intact if it's not there.")
                usage()
        else:
            print("Input file(s) doesn't exist!")
            usage()

    else:
        usage()

if __name__ == '__main__':
    Main()
