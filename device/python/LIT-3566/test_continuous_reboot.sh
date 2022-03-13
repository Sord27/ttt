#!/bin/bash

readonly LOWER_LIMIT=80
readonly UPPER_LIMIT=100

echo "Test pump force reboots"
echo "The pump is force rebooted after random time ($LOWER_LIMIT-$UPPER_LIMIT seconds) after start"

for i in {1..50}
do
    LOAD_WAIT=$(shuf -i $LOWER_LIMIT-$UPPER_LIMIT -n 1)
    echo $(date '+%Y-%m-%d %H:%M:%S') "INFO Iteration $i"
    echo $(date '+%Y-%m-%d %H:%M:%S') "INFO ssh into pump and force reboot"

    sshpass -p 'bam!ssh' ssh -o 'ServerAliveInterval 2' -p 22221 root@172.22.10.19 'reboot -f'

    echo $(date '+%Y-%m-%d %H:%M:%S') "INFO Wait $LOAD_WAIT seconds for pump to boot"
    sleep $LOAD_WAIT

    IS_SSH_AVAILABLE=$(sshpass -p 'bam!ssh' ssh -q root@172.22.10.19 -p 22221 exit && echo 1 || echo 0)

    if [[ $IS_SSH_AVAILABLE -ne 0 ]]; then
        echo $(date '+%Y-%m-%d %H:%M:%S') "INFO Successful ssh login."
    else
        echo $(date '+%Y-%m-%d %H:%M:%S') "INFO Failed ssh login. Manual pump check is required..."
        exit 1
    fi
done
