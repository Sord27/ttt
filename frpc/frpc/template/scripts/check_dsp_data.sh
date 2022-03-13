#!/bin/bash
. /bam/scripts/bamfunc.sh
leds=`bamio_get_key PLED`
srvr_led=${leds:0:1}
bamod_count=`pgrep bamod 2>/dev/null | wc -l`

[[ `get_log_level` -lt 1 ]] && baml 1 1minute &>/dev/null
dsp=`timeout 30 tail -n 0 -f /var/log/bamlog \
    | grep --line-buffered TAG_XPORT_SE_DSP_REPORT_4 2>/dev/null | wc -l`

echo "$srvr_led $bamod_count $dsp"
