# Flexible Remote Process Caller

## Summary

This is a small framework designed to make it easy to run short bash scripts
on a set of pumps returned by a SUMO query. 

## Installation

First of all, you need an environment with python 3.7. I recommend using miniconda for that. This repo contains a script (`scripts/install-conda.sh`) that automates miniconda installation for **bash**.
By default, *frpc* installs binaries into your python environment so that you can run it from anywhere on your system.

```
./scripts/install-conda.sh
bash # restart your shell

# Create and use conda environment called 'frpc'
conda create -n frpc python=3.7
conda activate frpc

# Install the script into your conda environment
make install
```

Once the installation process is finished, you can use the script from any directory on your machine:
```
conda activate frpc
frpc_script --help
```

## Development

If you don't want to install the script into your python environment, you can run it directly from the source folder. Make sure that you create conda environment beforehand.

```
export PYTHONPATH=.
./bin/frpc_script --help
```

Once you've made the desired changes, run `make check` to lint your code.

## Configuration

Before actually using the script you have to acquire a number of credentials:

### 1. Boson servers access

Navigate to a Confluence page on [Boson SSH Servers](https://selectcomfort.atlassian.net/wiki/spaces/SD/pages/73728141/Boson+SSH+Servers).
You can setup access to boson either via *Corporate* or *AWS VPN*. If you plan on using both *RPC* and *Boson* interfaces at the same time (currently only *frpc_deploy* does that) then you have to stick with **Corporate VPN**.
Once you finish with the setup process described on the Confluence page above make sure that everything works.
For that, run `ssh boson-boson49` in terminal, you should see something like this:

```
(frpc) denys@vbox:~/bamtools/frpc$ ssh boson-boson49
Warning: Permanently added 'boson-boson49' (ECDSA) to the list of known hosts.
Last login: Thu Apr 22 17:10:13 2021 from 172.25.3.252
 This instance is managed with AWS OpsWorks.

   ######  OpsWorks Summary  ######
   Operating System: Amazon Linux AMI release 2017.09
   OpsWorks Instance: boson-boson49
   OpsWorks Instance ID: 8b98cb48-a874-467c-9132-ca8270958a67
   OpsWorks Layers: Boson Cluster
   OpsWorks Stack: boson
   EC2 Region: us-east-1
   EC2 Availability Zone: us-east-1c
   EC2 Instance ID: i-04854419a9bf1a2fd
   Public IP: 
   Private IP: 172.25.3.223
   VPC ID: vpc-d39db9b4
   Subnet ID: subnet-d243b4ff

 Visit http://aws.amazon.com/opsworks for more information.
[denysromaniuksleepnumbercom@boson-boson49 ~]$ 
```

### 2. OPS Portal access

The script looks for a file called `.ops_creds.json` either in the current directory or in HOME. Simply copy `ops_creds.example.json` from the repository into a desired location and fill out accordingly.
If you don't have access to certain environment, you can simlpy remove it from `.ops_creds.json`.

### 3. SumoLogic access

If you plan on using the script to fetch results directly from Sumo you need to configure access keys for SumoLogic API. The script looks for a file called `.sumo_config.ini` either in the current directory or in HOME.

1. Open preferences page (https://service.us2.sumologic.com/ui/#/preferences).
2. Find 'My Access Keys' section and generate credentials via '+ Add Access Key' button.
3. Copy 'access_id' and 'access_key' to corresponding lines of `.sumo_config.ini` file as shown in `sumo_config.example.ini`.

## Included Programs

### frpc_script

```
usage: frpc_script [-h] [--devices-limit DEVICES_LIMIT] [--truncate]
                   [--sumo-time-offset SUMO_TIME_OFFSET]
                   [--sumo-time SUMO_TIME SUMO_TIME] [--interface {boson,rpc}]
                   [--boson-index BOSON_INDEX]
                   [--boson-range BOSON_RANGE BOSON_RANGE]
                   [--rpc-creds RPC_CREDS]
                   [--rpc-env {circle1,circle2,dev21,dev22,dev23,dev24,ops21,prod,qa21,qa22,qa23,stage,test}]
                   [--exec-processes EXEC_PROCESSES]
                   [--exec-output EXEC_OUTPUT] [-v] [--force] --script SCRIPT
                   [SCRIPT ...]
                   targeting

Run a bash script on a list of remote pumps

positional arguments:
  targeting             either a csv file exported from sumo (with a `mac'
                        field), a local sumoql file, an embedded sumoql file
                        (date-not-correct.sumoql, bamio-not-ready.sumoql,
                        connectivity-issues.sumoql), tageting:no_boson,
                        tageting:no_boson_m2

optional arguments:
  -h, --help            show this help message and exit
  --devices-limit DEVICES_LIMIT
                        overwrite devices limit
  --truncate            reduce targets amount to fit into devices limit
  --sumo-time-offset SUMO_TIME_OFFSET
                        query time offset, positive value in seconds, minimum
                        300
  --sumo-time SUMO_TIME SUMO_TIME
                        query start and end time, in UNIX timestamp
  --interface {boson,rpc}
                        interface to send remote commands
  --boson-index BOSON_INDEX
                        boson server index to use
  --boson-range BOSON_RANGE BOSON_RANGE
                        randomly generate boson index from the specified range
                        for every mac
  --rpc-creds RPC_CREDS
                        OPS portal credentials file in JSON format
  --rpc-env {circle1,circle2,dev21,dev22,dev23,dev24,ops21,prod,qa21,qa22,qa23,stage,test}
                        Cloud envoronment to use
  --exec-processes EXEC_PROCESSES
                        number of executors to run in parallel
  --exec-output EXEC_OUTPUT
                        write execution results to a .csv
  -v, --verbose         show debug messages
  --force               bypass the limit on 32 devices
  --script SCRIPT [SCRIPT ...]
                        either built-in script name (fix_date_not_correct.sh,
                        lbts_cbq.sh, bammit_restart.sh, diag.sh,
                        log_conn_issues.sh, check_network_connectivity.sh,
                        diag.sh.bak, bamstat.sh, restart_networking.sh,
                        reboot.sh, nop.sh, baml1.sh, get_version.sh,
                        tunnel_stop.sh, bamnet_start.sh, clear_boson_queue.sh,
                        log_bamio_not_ready.sh, tunnel_start.sh, get_mac.sh,
                        check_dsp_data.sh, ntpq.sh) or a path to a script
```

### frpc_deploy

```
usage: frpc_deploy [-h] [-v] [--force] [--boson-index BOSON_INDEX]
                   [--boson-range BOSON_RANGE BOSON_RANGE]
                   [--rpc-creds RPC_CREDS]
                   [--rpc-env {circle1,circle2,dev21,dev22,dev23,dev24,ops21,prod,qa21,qa22,qa23,stage,test}]
                   [--exec-processes EXEC_PROCESSES]
                   [--exec-output EXEC_OUTPUT] [--state-file STATE_FILE]
                   [--span-time SPAN_TIME] --start-time START_TIME
                   [--safety-time-buffer SAFETY_TIME_BUFFER]
                   [--install-time INSTALL_TIME] [--sumo-delay SUMO_DELAY]
                   [--batch-size BATCH_SIZE] [--dry-run]
                   {full,ptg} device_registry

Execute pre- and post-deploy activities.

positional arguments:
  {full,ptg}            deploy type that is being used
  device_registry       file that represents a list of devices participating
                        in the update. For a FULL deploy this should the
                        device registry file. For PTG/ETG deploy this should a
                        .csv file

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         show debug messages
  --force               bypass the limit on 32 devices
  --boson-index BOSON_INDEX
                        boson server index to use
  --boson-range BOSON_RANGE BOSON_RANGE
                        randomly generate boson index from the specified range
                        for every mac
  --rpc-creds RPC_CREDS
                        OPS portal credentials file in JSON format
  --rpc-env {circle1,circle2,dev21,dev22,dev23,dev24,ops21,prod,qa21,qa22,qa23,stage,test}
                        Cloud envoronment to use
  --exec-processes EXEC_PROCESSES
                        number of executors to run in parallel
  --exec-output EXEC_OUTPUT
                        write execution results to a .csv
  --state-file STATE_FILE
                        File to save to or load current state from
  --span-time SPAN_TIME
                        full deploy span time in minutes
  --start-time START_TIME
                        planned deploy time in UNIX timestamp
  --safety-time-buffer SAFETY_TIME_BUFFER
                        minimum possible time difference, in seconds, between
                        the start of a pre-deploy activity on a device and the
                        actual deploy
  --install-time INSTALL_TIME
                        maximum time it takes for the software to be fully
                        installed
  --sumo-delay SUMO_DELAY
                        time it takes for a newly created to get from a device
                        to SumoLogic
  --batch-size BATCH_SIZE
                        minimum processing batch size
  --dry-run             send NOP instead of the fix

This is a program for running pre- and post-deploy activities. It recovers
devices that have connectivity issues and are likely to fail the update. The
approach this program uses doesn't work in 100% of the cases, but it covers
most of them. It is capable of accompanying an ETG, PTG or full deploy.
Depending on the type of deploy, it may use your local AWS, OPS and boson
credentials so MAKE SURE to configure those beforehand.
```

## Use Cases

### Execute a Script on Remote Pumps

Before you run a script, you need to determine which interface to use:
* Use `--interface boson` if you need return code, stdout and stderr from your script.
* Use `--interface rpc` if 'fire-and-forget' approach is sufficient. Note, that *circle1* is used by default for this interface. If you need a different environment, use `--rpc-env`.

`frpc_script` has built-in scripts that you can run on remote pumps. They're listed in the description of the `--script` parameter:

```
  --script SCRIPT [SCRIPT ...]
                        either built-in script name (bammit_restart.sh,
                        restart_networking.sh, reboot.sh, nop.sh,
                        get_version.sh, tunnel_start.sh) or a path to a script
```

If you'd like write your own script, you can pass a filepath instead of a script name to the `--script` argument (e.g. `--script /tmp/test_scipt.sh`).

The list of target MAC addresses is specified within a *.csv* file, that contains a `mac` field. This is useful when you have a SUMO query that gives you a list of MACs as result like this:

```
_sourceCategory=boson/boson/messages
AND "bloh_soc_init"
AND "Resource temporarily unavailable"
OR "Dl timeout"
| parse "500-* " as mac | count by mac | fields mac
```

Say that you have a `failed-pumps.csv` that looks like this:

```
mac
64dba00eb7a7
CC04B40D3F26
CC04B40D41B5
```

Then the command to execute `nop.sh` would look like this:

```
frpc_script failed-pumps.csv --interface rpc --exec-processes 4 --script nop.sh
```

It's also possible to feed the query directly into the script if you want to avoid manually running and exporting query results from sumo. For this, you have to put the query text into a file and save it with the `.sumoql` extension. To execute the script, you would then have to run:

```
frpc_script failed-pumps.sumoql --interface rpc --exec-processes 4 --script nop.sh
```

### Retrive Command Results From Remote Pumps

Say that you need to retrieve firmware versions from a list of pumps. `get_version.sh` may be used for that. It simply outputs firmware versions in stdout. Boson interface can return the script return code, stdout and stderr contents back to us. To actually see them, we have to specify `--exec-output` parameter. The parameter will force the script to save execution results into a specified file.

```
frpc_script failed-pumps.csv --interface boson --exec-processes 4 --exec-output versions.csv \
    --script get_version.sh
```

As a result, `version.csv` should contain something similar to this:

```
"mac","returncode","success","stdout","stderr"
"cc04b40d3f26","","False","",""
"cc04b40d37d2","0","True","SE_500_zep4_5.0.18_2102111200_boson_GA
SE_500_rfs_10.0.13_2102111200_all_boson_GA
","Warning: Permanently added '[172.25.3.29]:39963' (ECDSA) to the list of known hosts.
"
"cc04b40d2e93","0","True","SE_500_zep4_5.0.18_2102111200_boson_GA
SE_500_rfs_10.0.13_2102111200_all_boson_GA
","Warning: Permanently added '[172.25.5.108]:42265' (ECDSA) to the list of known hosts.
"
"64dba00eb7a7","","False","",""
"64dba00f0949","","False","",""
"cc04b403ae07","0","True","SE_500_zep4_5.0.18_2102111200_boson_GA
SE_500_rfs_10.0.13_2102111200_all_boson_GA
","Warning: Permanently added '[172.25.5.147]:43927' (ECDSA) to the list of known hosts.
"
"cc04b40d41b5","0","True","SE_500_zep4_5.0.18_2102111200_boson_GA
SE_500_rfs_10.0.13_2102111200_all_boson_GA
","Warning: Permanently added '[172.25.4.185]:34891' (ECDSA) to the list of known hosts.
"
"cc04b40d4413","0","True","SE_500_zep4_5.0.18_2102111200_boson_GA
SE_500_rfs_10.0.13_2102111200_all_boson_GA
","Warning: Permanently added '[172.25.3.13]:45937' (ECDSA) to the list of known hosts.
"
```

### Fix *date not correct* Issue

To fix pumps that encountered the issue in the last 4 hours, you can run the following command:

```
frpc_script date-not-correct.sumoql \
    --interface boson \
    --exec-processes 48 \
    --exec-output date-not-correct-results-`date +%s`.csv \
    --script fix_date_not_correct.sh \
    --sumo-time-offset 14400 \
    --verbose
```

* The command above will produce a file called ``date-not-correct-results-`date +%s`.csv`` that should contain the execution results.
* `--sumo-time-offset 14400` tells the script to run embedded `date-not-correct.sumoql` SUMO query files over the last 4 hours.

### Flush boson-queue and restore boson tunnel

To restore boson connection on the environment scale, you can run the following command:

```
AWS_PROFILE=AWS_PROFILE_FOR_VPC_BUCKET frpc_script targeting:no_boson \
    --devices-limit DEVICES_LIMIT \
    --truncate \
    --interface rpc \
    --rpc-env RPC_ENV \
    --exec-processes EXEC_PROCESSES \
    --exec-output fix-no-boson-results-`date +%s`.csv \
    --verbose \
    --script clear_boson_queue.sh
```

* The script requires access to an S3 bucket that contains Device Registry files for the `RPC_ENV` environment.
* `DEVICES_LIMIT` is the maximum number of devices to process. Best to keep this value in the range from 1000 to 20000.
* `AWS_PROFILE_FOR_VPC_BUCKET` is the profile that has access to the necessary S3 bucket. 
* `RPC_ENV` is the environment from which to pull the Device Registry.
* `EXEC_PROCESSES` should be the number of DGs in the environment.

Environment names and the corresponding bucket names the script needs access to:

| Environment                | S3 Bucket Name             |
| -------------------------- | -------------------------- |
| dev21, dev22, dev23, dev24 | siq-dev-dev-vpc            |
| qa21, qa22, qa23           | siq-dev-qa-vpc             |
| ops21                      | siq-dev-ops-vpc            |
| circle1, circle2           | sc-corp-circle-vpc         |
| test                       | sc-corp-test-vpc           |
| stage                      | sc-corp-stage-vpc          |
| prod                       | zepp-prod-vpc              |

### Flush boson-queue and restore boson tunnel on M2 pumps

To restore boson connection on the environment scale, you can run the following command:

```
AWS_PROFILE=AWS_PROFILE_FOR_VPC_BUCKET frpc_script targeting:no_boson_m2 \
    --devices-limit DEVICES_LIMIT \
    --truncate \
    --interface rpc \
    --rpc-env RPC_ENV \
    --exec-processes EXEC_PROCESSES \
    --exec-output fix-no-boson-results-`date +%s`.csv \
    --verbose \
    --script lbts_cbq.sh
```

### Pre- and post-deploy activities

You may use `frpc_deploy` to execute activities that improve success rate of a PTG/full embedded software deploy.
Pre-deploy activities include the following actions:

| Activity name            | Query                      | Action                 |
| ------------------------ | -------------------------- | ---------------------- |
| connectivity_issues      | connectivity-issues.sumoql | reboot.sh              |
| no_boson                 | CSTAT files from boson     | tunnel_start.sh        |

Post-deploy activities include the following actions:

| Activity name            | Query                      | Action                 |
| ------------------------ | -------------------------- | ---------------------- |
| bamio_not_ready          | bamio-not-ready.sumoql     | reboot.sh              |

`frpc_deploy` has the following timings:

1. Fetch queries for pre-deploy activities (~25 minutes).
2. Execute pre-deploy activities.
3. Wait until `START_TIME` UNIX timestamp (until the deploy starts).
4. Wait `SPAN_TIME` (OVERTIME) minutes.
5. Wait `INSTALL_TIME` seconds (16 minutes by default) for the pumps to complete binaries installation.
6. Wait `SUMO_DELAY` seconds (5 minutes by default) for the sumo logs to propagate.
7. Fetch queries for post-deploy activities.
8. Execute post-deploy activities.

A typical command to execute the script:

```
frpc_deploy DEPLOY_TYPE DEVICE_REGISTRY \
    --rpc-env RPC_ENV \
    --exec-processes EXEC_PROCESSES \
    --span-time SPAN_TIME \
    --exec-output EXEC_OUTPUT \
    --start-time START_TIME
```

* `DEPLOY_TYPE` specifies the type of deploy. It can be either `full` or `ptg`. With full deploy `--span-time` option becomes effective and executes the activities in the specified number of minutes. It does the same way as the cloud send `TAG_CMD_RELOAD` to devices during overtime deploy. During `ptg` deploy the script executes activities ASAP.
* `DEVICE_REGISTRY` should point either to a device registry file from S3 (click *Run Device Registry to S3 Job* button in OPS Portal -> Tools, the file will appear in S3 `ACCNT-RPC_ENV-vpc/RPC_ENV/device-registry`) or a csv file that contains the list of MACs in PTG.
* `RPC_ENV` environment devices belong to.
* `EXEC_PROCESSES` number of parallel requests to REST API. Keep this value close to the number of DGs in the environment.
* `SPAN_TIME` is only applicable for `full` deploys. Should be the same as `OVERTIME` value on the cloud. If don't want the script to run activities this long, you can specify a comfortable value for you, but make sure to interrupt the script with *Ctrl+C* once it finishes the pre-deploy activities. After that you can change the `span_time` value in the newly created `state-file-DEPLOY_TYPE-deploy-DATETIME.json` and pass the changed file as `--state-file`.
* `EXEC_OUTPUT` is the base name for csv files that will contain information about affeted pumps during pre- and post-deploy activities. For example, if you specify `prod-5.0D-deploy.csv`, then the script will create two files called `prod-5.0D-deploy.connectivity_issues.csv` and `prod-5.0D-deploy.no_boson.csv` in you current working directory once it finishes the pre-deploy activities.
* `START_TIME` is the planned dpeloy start time in UNIX timestamp. It has to be at least `SPAN_TIME * 60 + SAFETY_TIME_BUFFER + 700` seconds in the future. You can use this bash command to quickly generate a valid UNIX timestamp: ``echo $(( `date +%s` + 300 * 60 + 15 * 60 + 700 ))``.

```
frpc_deploy full 'DR_07-15-2021-20 15 48' \
    --rpc-env prod \
    --exec-processes 32 \
    --span-time 120 \
    --exec-output prod-5.0D-deploy.csv \
    --start-time 1627131080
```

Once the script finishes the pre-deploy activities, you can terminate it. Make sure to save the state file. You can use it later to modify deploy parameters and restore the script from the state it was interrupted in. You can use the `--state-file` option to restore the state.
