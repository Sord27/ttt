# Create CREQ files

## Summary

This script was created to address the Rabbit M2 logging issue where pumps were not automatically connecting to the boson after a reboot.
It creates CREQ files for the specified mac address range. These files tell the pumps to connect to the boson right after the boot.

## Usage

The script makes PUT requests into the `siq-dev-boson-devices` S3 bucket at a hardcoded limit of 100 requests per second.
For every mac address it creates a file with prefix `s3://siq-dev-boson-devices/creq/{mac}` with contents `BOSON=true`.
Make sure to [set up AWS CLI Access](https://selectcomfort.atlassian.net/wiki/spaces/SD/pages/1642922188/AWS+Access+using+Okta+SSO+QA+team#CLI-Access) before starting the script.

```
gimme-aws-creds    # select role role-siq-qa-teamdevice
pip3 install -r requirements.txt
AWS_PROFILE=siq-dev-qa-teamdevice python3 create_creq_files.py --threads 64 64dba0f00000 64dba0f186a0
```
