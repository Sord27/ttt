#!/bin/bash

readonly PUMP_LOAD_WAIT=100
readonly LOWER_LIMIT=20
readonly UPPER_LIMIT=60
readonly NUMBER_OF_ITERATIONS=10
readonly OUTLET_ADDRESS=172.22.10.19:8161
readonly OUTLET=1

echo "Test pump power cycles"
echo "The pump is powered off $LOWER_LIMIT-$UPPER_LIMIT seconds after being turned on. 10 iterations per each second"

for wait_seconds in {$LOWER_LIMIT..$UPPER_LIMIT}
do
    echo "============================="
    for i in {1..$NUMBER_OF_ITERATIONS}
    do
        echo "Iteration $i"
        ./cyberpower_pdu $OUTLET_ADDRESS $OUTLET off && sleep 2
        ./cyberpower_pdu $OUTLET_ADDRESS $OUTLET on

        echo $(date '+%H:%M:%S') "INFO Delay $wait_seconds seconds"
        sleep $wait_seconds

        ./cyberpower_pdu $OUTLET_ADDRESS $OUTLET off && sleep 2
        ./cyberpower_pdu $OUTLET_ADDRESS $OUTLET on

        echo $(date '+%H:%M:%S') "INFO Wait $PUMP_LOAD_WAIT seconds for pump to boot"
        sleep $PUMP_LOAD_WAIT

        IS_SSH_AVAILABLE=$(sshpass -p 'bam!ssh' ssh -q root@172.22.10.19 -p 22221 exit && echo 1 || echo 0)

        if [[ $IS_SSH_AVAILABLE -ne 0 ]]; then
            echo $(date '+%H:%M:%S') "INFO Successful ssh login."
        else
            echo $(date '+%H:%M:%S') "INFO Failed ssh login. Manual pump check is required..."
            exit 1
        fi
    done
done