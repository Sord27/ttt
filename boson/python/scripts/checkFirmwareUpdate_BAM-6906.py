'''
# File 			: checkFirmwareUpdate_BAM-6906.py
# Description 	: Check firmware versions by comparing output from 'bio MFWL' and 'bio PBVR/PVER' commands on given device,
				: if it's same then do nothing(Success) else reboot the pump and check firmware versions again.
# Dependencies  : Unix OS(Linux or MAC), Python 2.7, pip, pexpect module (You can install it by running command "pip install pexpect")
				: Your boson login and password required to replace XXX.
# How to Run    : Run command "python checkFirmwareUpdate_BAM-6906.py"
# Output		: It will display k20/ble firmware versions and status(success/FAILURE) on the terminal.
# Warning Note  : This script would not run on Windows.
'''

import pexpect
import time

deviceID = raw_input('Please enter device ID: ')
deviceID = deviceID.lower().replace(' ','')

child = pexpect.spawn('ssh -p 6022 XXX@boson.bamlabs.com')			# enter your boson login
#child.maxread=1000
i = child.expect(['hello','password: ','(yes/no)? '])
if i==0:
	print "Got yes/no?"
	child.sendline('yes')
	child.expect('password: ')

child.sendline('XXX')													# enter your boson password

child.expect('$')
child.sendline('bamssh '+ deviceID)

child.expect('devid '+deviceID)
child.expect([' found','port '])
if child.before[-3:]=='not':
	print "Not connected to boson"
	child.expect('$')
	child.sendline('exit')
	child.kill(0)
	exit(1)

i=0
i = child.expect(['password: ','(yes/no)? '])
if(i==1):
	if(child.before[-1]!= "s"):
		child.sendline('yes')

child.expect('password: ')
child.sendline('bam!ssh')

child.expect('~# ')
child.sendline('bio MFWL')

try:
	child.expect(['fw_images','available'])
	
	i = child.before
	if child.before[-2]=='t':
		child.expect('~# ')
		print "bamio isn't available"
		child.sendline('exit')
		child.expect('closed.')
		child.sendline(' ')
		child.expect('$')
		child.sendline('exit')
		child.kill(0)
		exit(1)

	child.expect('>')
	i = child.before			# No. of fw_images
	fw_image = i.split('<')
	fw_image = fw_image[1]

except:
	print "Firmware List<[error]>"

valid_image = True

# For GVB
if(fw_image=='2'):
	print fw_image

	child.expect('>')
	i = child.before		# gvb-ble
	ble = i.split('<')
	ble = ble[1]

	child.expect('>')
	i = child.before		# gvb-k20
	k20 = i.split('<')
	k20 = k20[1]

# For SP1/SP2
elif (fw_image=='5'):
	print fw_image
	child.expect('>')
	i = child.before		# sp1-ble
	ble = i.split('<')
	ble = ble[1]

	child.expect('>')
	i = child.before		# foundation
	
	child.expect('>')
	i = child.before		# sp1-k20
	k20 = i.split('<')
	k20 = k20[1]

# Not valid number of fw_images
else:
	valid_image = False
	print "Couldn't find sufficient number of images!"


if valid_image:

	child.sendline('bio factory')

	child.expect('k20 vers')
	i = child.before
	actual_k20 = i.split('PVER')
	actual_k20 = actual_k20[1].replace(" ","")

	child.expect('ble vers')
	i = child.before
	actual_ble = i.split('PBVR ')
	actual_ble = actual_ble[1].replace(" ","")

	print k20, actual_k20		# Print K20 firmware version
	print ble, actual_ble		# Print ble firmware version

	
	if(k20==actual_k20 and ble==actual_ble):
		print "success"
	else:
		child.sendline('bio prbt 0')
		print "Rebooting pump..."
		time.sleep(30)
		child.sendline('bio factory')

		child.expect('k20 vers')
		i = child.before
		actual_k20 = i.split('PVER')
		actual_k20 = actual_k20[1].replace(" ","")

		child.expect('ble vers')
		i = child.before
		actual_ble = i.split('PBVR ')
		actual_ble = actual_ble[1].replace(" ","")

		print k20, actual_k20		# Print K20 firmware version
		print ble, actual_ble		# Print ble firmware version
		if(k20==actual_k20 and ble==actual_ble):
			print "Updated firmware successfully!"
		else:
			print "FAILURE!"

child.sendline('exit')
child.expect('$')
child.sendline('exit')
child.kill(0)
exit(1)
