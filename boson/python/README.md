## Synopsis

This scripts folder contains python scripts which would help to run specific **commands** on different devices via **boson server**. 
It also contains scripts to **parse bamlog file** to collect device list with specific kind of error messages(e.g. BAM-6905, BAM-6915).

## Code Example

This connects to the openbsd ftp site and downloads the recursive directory listing.

import pexpect
child = pexpect.spawn('ssh -p 6022 XXX@boson.bamlabs.com')
child.expect('password: ')
child.sendline('anonymous')
child.expect('Password:')
child.sendline('XXX')
child.expect('$ ')
child.sendline('bamssh <deviceID>')
child.interact()

## Motivation

This kind of expect python scripts help a lot to automate tedious manual tasks for which someone has to run same set of commands on number of devices. After production(launching new release to customers) if we are facing any issues and it can be fixed by running bunch of commands on those devices then these scripts are very useful for that. 

## Installation

To run these scripts, you will require below tools.
1) Mac/Linux OS
2) Python 2.7, pip, pexpect

### For Mac OS
1) To install pip : sudo easy_install pip
2) To install pexpect : pip install pexpect  or   easy_install pexpect

### For Linux OS
1) To install pip : sudo apt-get install pip
2) To install pexpect : sudo pip install pexpect

## API Reference

Depending on the size of the project, if it is small and simple enough the reference docs can be added to the README. For medium size to larger projects it is important to at least provide a link to where the API reference docs live.

## Tests

To run "stopBAM" command on a list of devices from a file(e.g. deviceList.txt).

Command  :  python stopBAM.py 

Output   :  Dhruvs-MacBook-Pro:scripts dhruvkakadiya$ python stopBAM.py 
			--------------------------------------------------
			Device No.1 Id: cc04b402f3dd
			success
			--------------------------------------------------
			Device No.2 Id: cc04b4033bc5
			Not connected to boson
			--------------------------------------------------
			Device No.3 Id: cc04b4025488
			Not connected to boson
			--------------------------------------------------
			Done


To run "startBAM" command on a list of devices from a file(e.g. deviceList.txt).

Command  :  python startBAM.py 

Output   :  Dhruvs-MacBook-Pro:scripts dhruvkakadiya$ python stopBAM.py 
			--------------------------------------------------
			Device No.1 Id: cc04b402f3dd
			success
			--------------------------------------------------
			Device No.2 Id: cc04b4033bc5
			Not connected to boson
			--------------------------------------------------
			Device No.3 Id: cc04b4025488
			Not connected to boson
			--------------------------------------------------
			Done

## Contributors

References :
	pexpect in python : https://pexpect.readthedocs.io/en/stable/
					  :	http://pexpect.sourceforge.net/doc/
	expect in shell   : https://www.pantz.org/software/expect/expect_examples_and_tips.html

If you find any difficulties, feel free to contact on "dhruv@bamlabs.com".

## License

A short snippet describing the license (MIT, Apache, etc.)
