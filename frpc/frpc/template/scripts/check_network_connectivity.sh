#!/bin/sh

# Source the local-most functions file.
#
_LOCALPATH=${0%/*}
_FUNCTIONS=/bam/scripts/bamfunc.sh
if [ -f ${_FUNCTIONS} ]; then
	. ${_FUNCTIONS}
else
	logger -p local1.error -t "$0" "missing ${_FUNCTIONS} file"
	exit 1
fi

a=$(ping 8.8.8.8 -c 10 | grep "100% packet loss")
if [ -n "$a" ]
then
        bam_log_error "Failed to ping 8.8.8.8; no network connectivity."
        c=$(arp -n | grep "wlan" | grep -oE '^[0-9.]+ ')
        echo "Pinging router at " $c
        for i in {1..5}
        do
            d=$(ping $c -c 10)
        done
fi

d=$(ping 8.8.8.8 -c 10 | grep " 0% packet loss")
if [ -n "$d" ]
then
        bam_log_info "Pinged 8.8.8.8; trying to update config."
        b=$(bamstat | grep "server:" | grep "test")
        if [ -n "$b" ]
        then
                bam_log_error "Test config file is present; trying to fetch valid config file via prepBAM"
                pkill -9 prepBAM
                prepBAM &
        fi
fi

