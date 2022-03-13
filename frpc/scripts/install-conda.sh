#!/bin/bash


error() {
    >&2 echo "Error: $1"
    exit 1
}


script_name=Miniconda3-latest-Linux-x86_64.sh
script_path="/tmp/$script_name"
conda_path="$HOME/.miniconda3"
wget --output-document "$script_path" \
    "https://repo.anaconda.com/miniconda/$script_name" \
    || error "failed to fetch conda binaries"
chmod -v +x "$script_path" || error "failed to fetch conda binaries"
"$script_path" -b -p "$conda_path" || error "installation failed"
conda="$conda_path/bin/conda"
"$conda" init || error "failed to modify the .bashrc"
"$conda" config --set auto_activate_base false

echo
echo " *** Please, restart you shell now."
echo
