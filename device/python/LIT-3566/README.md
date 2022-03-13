# Manage remote power distribution unit (tested on CyberPower PDU41008)
**cyberpower_pdu** - manages remote outlets
## Requirements
	$ sudo apt install snmp snmp-mibs-downloader
## Usage

	./cyberpower_pdu [agent]
	./cyberpower_pdu [agent] [outlet_num|outlet_name]
	./cyberpower_pdu [agent] [outlet_num|outlet_name] [action]
**cyberpower_pdu** script runs on top of [snmpwalk] and [snmpset] to manage
outlets.
## Actions

**1** or **on**
	Turn On.

**2** or **off**
	Turn Off.

**3** or **reboot**
	Reboot.

**4** or **cancel**
	Cancel pending command.

## Examples

Lists all outlets:

	$ ./cyberpower_pdu 172.22.10.19:8161
	Outlet1
	Outlet2

Get status for the first outlet:

	$ ./cyberpower_pdu 172.22.10.19:8161 1
	ON

Turn off the second outlet

	$ ./cyberpower_pdu 172.22.10.19:8161 2 off
	OFF

