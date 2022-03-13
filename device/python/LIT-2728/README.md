Control script first cleans old result file (specified in -o param), then runs the query to SUMO (specified in -q param), and then, if query result is not empty, runs action script (specified in -a param) and sends e-mails from mailbox specified in credentials.crd file to all the addresses specified in contacts.ctc file. Each e-mail will have a result file attached to it. -f and -t params specify lower and upper date limits for a query. To run query only (without any action), use --check_only option. To block sending e-mails, use --no_emails option.

Example command line:
python3 controlScript.py -f 03/04/2021 -t 04/04/2021 -a reboot_bam_remotely.sh -o output.csv -q bad_connectivity.sumoql --no_emails
