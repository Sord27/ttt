#!/bin/bash

readonly HOURS_TO_RUN=1
readonly LOWER_LIMIT=0
readonly UPPER_LIMIT=20
readonly OUTLET_ADDRESS=172.22.10.19:8161
readonly OUTLET=1

echo "Test pump power cycles"
echo "The pump is powered off $LOWER_LIMIT-$UPPER_LIMIT seconds after being turned on"
echo "=========================================================="

end=$((SECONDS+3600*HOURS_TO_RUN)) # time to run

while [ $SECONDS -lt $end ]; do
    wait_seconds=$(shuf -i $LOWER_LIMIT-$UPPER_LIMIT -n 1)
    ./cyberpower_pdu $OUTLET_ADDRESS $OUTLET on
    sleep $wait_seconds
    ./cyberpower_pdu $OUTLET_ADDRESS $OUTLET off && sleep 2

    echo $(date '+%H:%M:%S') "INFO Delay $wait_seconds seconds"
done
