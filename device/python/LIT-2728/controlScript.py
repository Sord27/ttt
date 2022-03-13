# This is control Python script

import os
import argparse
import time
import datetime
import subprocess
from remote_script_execute import log
import threading
from email_sender import send_email as se

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--from_time', help='Timestamp in %d/%m/%Y format')
parser.add_argument('-t', '--to_time', help='Timestamp in %d/%m/%Y format')
parser.add_argument('-o', '--output_file', help='Filename to write result in csv format')
parser.add_argument('-a', '--action_script', help='Filename of script to be executed on boson')
parser.add_argument('-c', '--check_only', action='store_true', help='Run query only (no pump reboots/emails)')
parser.add_argument('-q', '--query', help='Sumo query to run')
parser.add_argument('--no_emails', action='store_true', help='Do not send e-mails')
arguments = parser.parse_args()

from_time = arguments.from_time
to_time = arguments.to_time
output_file = arguments.output_file
output_file_ext = output_file.split(".")[1]
check_only = arguments.check_only
prj_dir = os.getcwd()


def search_files(dir_path, extension):
    file_list = []
    for f in os.listdir(dir_path):
        if f.endswith(".{}".format(extension)):
            file_list.append(f)
    if file_list:
        log.info("Files found:", file_list)
    else:
        log.warn("Directory list is empty")
        exit(1)
    return file_list


def thread_remote_execute():
    log.info("Remote execution started")
    remote_execute_path = prj_dir + "/remote_script_execute"
    remote_execute_files = search_files(prj_dir, output_file_ext)

    for file in remote_execute_files:
        remote_execute_cmd = "python3 {}/remote_script_execute.py {}/{} {}".format(remote_execute_path, remote_execute_path, arguments.action_script, file)
        log.info(remote_execute_cmd)
        subprocess.run(remote_execute_cmd, shell=True, check=True)

    log.info("Remote execution finished")


def thread_send_email():
    if arguments.no_emails:
        return

    log.info("Sending email started")
    email_sender_path = prj_dir + "/email_sender"
    creds = search_files(email_sender_path, "crd")
    creds = email_sender_path + "/" + "".join(creds)
    contacts = search_files(email_sender_path, "ctc")
    contacts = email_sender_path + "/" + "".join(contacts)

    send_email_cmd = "python3 {}/send_email.py -cr {} -ct {}".format(email_sender_path,
                                                                    creds,
                                                                    contacts)
    send_email_cmd = send_email_cmd + " -at \""
    attachments = search_files(prj_dir, output_file_ext)
    for attach in attachments:
        attach = prj_dir + "/" + attach + " "
        send_email_cmd = send_email_cmd + attach
    send_email_cmd = send_email_cmd[:-1]
    send_email_cmd = send_email_cmd + "\""

    subprocess.run(send_email_cmd, shell=True, check=True)

    log.info("Sending email finished")


def run_sumo_query():
    sd = prj_dir + "/sumo_helper"
    qd = sd + "/queries"

    log.info("Prepare queries in {}".format(qd))
    env_file = search_files(sd, "env")
    env_file = sd + "/" + "".join(env_file)
    etables, ptypes = se.read_file(env_file)

    gen_file = search_files(qd, "genq")
    gen_file = qd + "/" + "".join(gen_file)
    with open(gen_file, mode='r', encoding='utf-8') as sumo_generic:
        gen_data = sumo_generic.read()

    for etable, ptype in zip(etables, ptypes):
        filename = qd + "/" + ptype + ".sumoql"
        with open(filename, mode='w', encoding='utf-8') as sumo_file:
            sumo_file.write(gen_data.format(etable, ptype))

    from_time_ms = int(time.mktime(datetime.datetime.strptime(from_time, "%d/%m/%Y").timetuple())) * 1000
    to_time_ms = int(time.mktime(datetime.datetime.strptime(to_time, "%d/%m/%Y").timetuple())) * 1000
    log.info("Time in ms. From {} to {}".format(from_time_ms, to_time_ms))
    log.info("Start sumo query")

    log.info("Started query: {}".format(arguments.query))
    sumo_search_cmd = "python3 {}/get_search_job.py --q {} -f {} -t {} -o {}_{}".format(sd,
                                                                                       (qd + "/" + arguments.query),
                                                                                       from_time_ms,
                                                                                       to_time_ms,
                                                                                       arguments.query,
                                                                                       output_file)
    subprocess.run(sumo_search_cmd, shell=True, check=True)


if __name__ == '__main__':
    log.info("Start script")

    if os.path.isfile("{}_{}".format(arguments.query, arguments.output_file)):
        log.info("removing previously existing output file: {}_{}".format(arguments.query, arguments.output_file))
        os.remove("{}_{}".format(arguments.query, arguments.output_file))

    run_sumo_query()

    if not arguments.check_only:
        log.info("Searching for result files")
        output_list = search_files(prj_dir, output_file_ext)

        output_list_reb = []

        threads = [threading.Thread(target=thread_send_email, args=()),
                   threading.Thread(target=thread_remote_execute, args=())]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()
