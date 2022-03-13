#!/bin/bash


function log_info() {
    1>&2 echo -e "$0: \033[0;32minfo\033[0m: $@"
}


function log_warn() {
    1>&2 echo -e "$0: \033[0;33mwarn\033[0m: $@"
}


function error() {
    1>&2 echo -e "$0: \033[0;31merror\033[0m: $@"
    exit 1
}


salt=s`date +%s`


function get_boson_line() {
    local ssh_command=$1
    local mac=$2

    [[ -z $ssh_command ]] && error "ssh_command expected"
    [[ -z $mac ]] && error "mac expected"

    bash -c "`cat $(which boson)`" "echo $ssh_command$salt" $mac | tail -n 1
}


function boson_cmd() {
    local ssh_command=$1
    local mac=$2
    local line=`get_boson_line "$ssh_command" $mac`

    if [[ $line == *$salt* ]] && [[ $line != *boson:* ]]; then
        local cmd=`echo "$line" | sed "s/$salt//" | sed "s/\s$mac//"`

        log_info "running cmd: $cmd ${@:3}"

        if [[ $DRY_RUN != yes ]]; then
            sshpass -p "bam!ssh" $cmd ${@:3}
        else
            log_info "DRY_RUN=yes"
        fi

        return 0
    else
        log_warn "$mac: $line"

        return 1
    fi
}


function boson_ssh() {
    local mac=$1

    boson_cmd ssh $mac $mac ${@:2}

    return $?
}


function boson_scp() {
    local mac=$1

    boson_cmd scp $mac ${@:2}

    return $?
}


macs="{{{MACS}}}"

if [[ `echo -n "$macs" | wc -c` -eq 10 ]]; then
    log_info "no macs were provisioned with the script, assuming from args"
    macs=$@
fi

log_info "caching ssh configs"

connected_macs=
stats_connected=0
stats_total=0

for mac in $macs; do
    mac=${mac,,}
    line=`get_boson_line ssh $mac`

    if [[ $line == *$salt* ]]; then
        connected_macs="$connected_macs $mac"
        (( stats_connected += 1 ))
    else
        log_warn "$mac: $line"
    fi

    (( stats_total += 1 ))
done

log_info "$stats_connected out of $stats_total devices are connected"

log_info "running rebootBAM"

stats_processed=0

for mac in $connected_macs; do
    boson_ssh $mac "/bam/scripts/rebootBAM"

    (( stats_processed += 1 ))
    log_info "processed $stats_processed out of $stats_connected"
done

