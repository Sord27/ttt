#!/bin/bash
. /bam/scripts/bamfunc.sh
bam_log_error 'Telling pump to reboot immediately'
sleep 1
bam_log_error 'usb</dev/ttyACM0> open error No such file or directory'
bam_log_error 'BAM I/O not ready'

