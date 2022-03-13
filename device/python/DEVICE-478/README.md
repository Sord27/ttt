# SleepIQ Account CLI Application #

This CLI script generates, creates, and deletes SleepIQ accounts. This script uses both the REST API and the Backoffice Administration Page. Manipulation of the Backoffice Administration Page is done using [`chromedriver`](https://sites.google.com/a/chromium.org/chromedriver/) and [Selenium](https://selenium.dev/).

## Requirements ##

The script must be run using [Python 3.7+](https://www.python.org/downloads/) on a *nix based system. This script is not support on Windows.

The required Python Packages can be installed using the following command in the script directory:

```bash
pip3 install -r requirements.txt
```

In addition to the required Python packages, `chromedriver` is also required.

### macOS ###

[`brew`](https://brew.sh) is the recommended way to install `chromedriver`.

```bash
brew cask install chromedriver
```

### Ubuntu/Debian ###

```bash
sudo apt install -y chromium-chromedriver
```

## Usage ##

```
usage: sleepiq_account.py [-h] {config,generate,create,delete} ...

Script to create a SleepIQ account and perform all of the necessary steps to
get a bed online. This script can also generate a 'bam-init.conf' file that
can be used to get a real pump online, and a 'bam.conf' which is used by a
virtualized pump to connect to cloud.

positional arguments:
  {config,generate,create,delete}
    config              Create a config.yaml file to hold specific settings.
    generate            Generate a configuration file
    create              Create an account using pregenerated information
    delete              Delete an account

optional arguments:
  -h, --help            show this help message and exit

For more information on any of the above commands, check their specific help
responses.
```

### Configuration ###

```
usage: sleepiq_account.py config [-h] [-c CONFIG] [-v]
                                 [-e {alpha,circle1,circle2,dev21,dev22,dev23,dev24,ops21,prod,qa21,qa22,qa23,stage,test}]
                                 [-r REFERENCE] [--app APP] [--rfs RFS]
                                 [-u USERNAME] [-p PASSWORD] [--ssid SSID]
                                 [--psk PASSWORD]

Generate a configuration file for use with the account creation script.
Information in this file can be configured directly from the arguments, or
edited from the empty file.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Configuration file used to define environment and
                        credentials. Defaults to 'config.yaml'
  -v, --verbose         Adjust verbosity
  -e {alpha,circle1,circle2,dev21,dev22,dev23,dev24,ops21,prod,qa21,qa22,qa23,stage,test}, --environment {alpha,circle1,circle2,dev21,dev22,dev23,dev24,ops21,prod,qa21,qa22,qa23,stage,test}
                        SleepIQ cloud environment to create account in.
                        Defaults to 'circle1'
  -r REFERENCE, --reference REFERENCE
                        Default Account Reference/Name. Defaults to
                        'auto_generated'

Version:
  --app APP             Bammit Application Version to set for the device.
                        Defaults to '[latest]'
  --rfs RFS             Bammit RFS Version to set for the device. Defaults to
                        '[latest]'

Backoffice:
  -u USERNAME, --username USERNAME
                        Username for Backoffice account
  -p PASSWORD, --password PASSWORD
                        Password for Backoffice account

WiFi:
  --ssid SSID           WiFi network SSID
  --psk PASSWORD        WiFi network Password
```

### Generate Account ###

```
usage: sleepiq_account.py generate [-h] [-c CONFIG] [-v] [-n FIRST LAST]
                                   [-e XXXXXX@XXXX.XXX] [-p PASSWORD]
                                   [-m XX:XX:XX:XX:XX:XX]
                                   [--internal_id XX:XX:XX:XX:XX:XX]
                                   [--generation {legacy,360}] [--ssid SSID]
                                   [--psk PASSWORD] [-o OUTPUT]

Generate a configuration file for use with this script. If any of these values
are not defined, they are randomly generated.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Configuration file used to define environment and
                        credentials. Defaults to 'config.yaml'
  -v, --verbose         Adjust verbosity
  -o OUTPUT, --output OUTPUT
                        Output File. Defaults to 'account.json'

Account Details:
  -n FIRST LAST, --name FIRST LAST
                        First and Last name of user to create
  -e XXXXXX@XXXX.XXX, --email XXXXXX@XXXX.XXX
                        Email to use for the generated account.
  -p PASSWORD, --password PASSWORD
                        Password to create account with

Order Details:
  -m XX:XX:XX:XX:XX:XX, --mac XX:XX:XX:XX:XX:XX
                        MAC Address of Pump to create
  --internal_id XX:XX:XX:XX:XX:XX
                        MAC Address to use for the Internal ID. Defaults to
                        '00:11:de:ad:be:ef'
  --generation {legacy,360}
                        Product Generation. Defaults to '360'

WiFi:
  --ssid SSID           WiFi network SSID
  --psk PASSWORD        WiFi network Password
  ```

### Create Account ###

```
usage: sleepiq_account.py create [-h] [-c CONFIG] [-v] [-i INPUT]
                                 [--init BAM_INIT] [-o BAM_CONF]

Create an account in the SleepIQ backend to get a pump online with the
necessary information. This will create all of the necessary objects to get a
360 pump online with a sleeper in the bed.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Configuration file used to define environment and
                        credentials. Defaults to 'config.yaml'
  -v, --verbose         Adjust verbosity
  -i INPUT, --input INPUT
                        Account information used to create account in the
                        backend. Defaults to 'account.json'
  --init BAM_INIT       Where to store bam-init.conf file. Defaults to bam-
                        init.conf
  -o BAM_CONF, --output BAM_CONF
                        Output File. Defaults to 'bam.config'
```

### Delete Account ###

```
usage: sleepiq_account.py delete [-h] [-c CONFIG] [-v] account [account ...]

Delete SleepIQ account using Account ID

positional arguments:
  account               SleepIQ Account ID to delete. Can pass multiple IDs to
                        delete more than one ID at a time.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Configuration file used to define environment and
                        credentials. Defaults to 'config.yaml'
  -v, --verbose         Adjust verbosity
```
