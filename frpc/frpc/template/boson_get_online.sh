#!/bin/bash


function list_suffixes() {
    local suffixes=($1)
    local offset=$2
    local step=$3

    for i in `seq $offset $step $(( ${#suffixes[@]} - 1 ))`; do
        suffix=${suffixes[$i]}
        1>&2 echo "suffix=$suffix"
        find /var/run/cstat/$suffix -type f -name "????????????" -printf "%f\n"
    done
}


function get_filename() {
    local offset=$1
    echo "/tmp/$filename_magic.$offset"
}


filename_magic=`head /dev/urandom | tr -cd [:alnum:] | head -c 8`
# {{{suffixes}}}

if [[ -z $suffixes ]]; then
    suffixes=`for i in {0..255}; do printf "%02x " $i; done`
fi

threads=5
suffixes_arr=($suffixes)
[[ ${#suffixes_arr[@]} -lt $threads ]] && threads=${#suffixes_arr[@]}
offsets=`seq 0 $(( threads - 1 ))`

for offset in $offsets; do
    filename=`get_filename $offset`
    list_suffixes "$suffixes" $offset $threads > "$filename" &
done

wait `jobs -p`

for offset in $offsets; do
    filename=`get_filename $offset`
    cat "$filename"
    rm "$filename"
done
