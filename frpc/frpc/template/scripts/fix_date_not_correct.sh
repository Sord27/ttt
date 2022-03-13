#!/bin/bash

DAY_ZERO=1628847210

ts=`date +%s`

if [[ $ts -gt $DAY_ZERO ]]; then
    echo "date already set: $ts"
    exit 0
fi

initbam_count=`pgrep initBAM | wc -l`

if [[ $initbam_count -lt 1 ]]; then
    echo "found $initbam_count initBAMs running, bailing"
    exit 1
elif [[ $initbam_count -gt 1 ]]; then
    echo "found $initbam_count initBAMs running, killing them"
    pkill -9 initBAM
    /bam/scripts/initBAM &>/dev/null &
fi

/bam/scripts/bamnet start &>/dev/null &
echo "started bamnet"
