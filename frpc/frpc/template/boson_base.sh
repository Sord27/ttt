#!/bin/bash


function log_date() {
    date +"%Y-%m-%d %H:%M:%S,666"
}


function log_info() {
    1>&2 echo -e "`log_date`: \033[1;32mINFO\033[0m: `hostname`: $@"
}


function log_warn() {
    1>&2 echo -e "`log_date`: \033[1;33mWARNING\033[0m: `hostname`: $@"
}


function error() {
    1>&2 echo -e "`log_date`: \033[1;31mERROR\033[0m: `hostname`: $@"
    exit 1
}


salt=s`date +%s`


function get_boson_line() {
    local ssh_command=$1
    local mac=${2,,}

    [[ -z $ssh_command ]] && error "ssh_command expected"
    [[ -z $mac ]] && error "mac expected"

    cstat=/var/run/cstat/`tail -c 3 <<< $mac`/$mac

    if [[ -f $cstat ]]; then
        bash -c "`cat $(which boson)`" "echo $ssh_command$salt" $mac \
            | tail -n 1

        return $?
    else
        echo "boson: no CSTAT file for $mac"
        return 1
    fi
}


function boson_cmd() {
    local tag=$1
    local ssh_command=$2
    local mac=$3
    local stdout_path=$results_dir/$mac/stdout.$tag
    local stderr_path=$results_dir/$mac/stderr.$tag
    local rc_path=$results_dir/$mac/rc.$tag
    local line=`get_boson_line "$ssh_command" $mac`

    if [[ $line == *$salt* ]] && [[ $line != *boson:* ]]; then
        local cmd=`echo "$line" | sed "s/$salt//" | sed "s/\s$mac//"`

        log_info "running cmd: $cmd ${@:4}"

        if [[ $DRY_RUN != yes ]]; then
            timeout 15m sshpass -p "bam!ssh" $cmd "${@:4}" 2>$stderr_path \
                | tee $stdout_path
            
            rc=${PIPESTATUS[0]}
            echo -n $rc > $rc_path
            return $rc
        else
            log_info "DRY_RUN=yes"
            return 0
        fi
    else
        log_warn "$mac: $line"

        return 1
    fi
}


function boson_ssh() {
    local tag=$1
    local mac=$2

    boson_cmd $tag ssh $mac $mac "${@:3}"

    return $?
}


function boson_scp() {
    local tag=$1
    local mac=$2

    boson_cmd $tag scp $mac "${@:3}"

    return $?
}


function boson_cache() {
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
}


function boson_parse_args() {
    if [[ `echo -n "$macs" | wc -c` -eq 10 ]]; then
        error "no macs were provisioned with the script, bailing."
    fi
}


function boson_init() {
    pull_dir=.
    results_dir=$pull_dir/results

    boson_parse_args

    local macs_array=($macs)
    connected_macs=$macs
    stats_connected=${#macs_array[@]}
}


macs="{{{macs}}}"
# {{{macs}}}
stats_processed=0
boson_init
for mac in $connected_macs; do
    mkdir -p $results_dir/$mac
    # {{{iter_body}}}
    (( stats_processed += 1 ))
    log_info "processed $stats_processed out of $stats_connected"
done
