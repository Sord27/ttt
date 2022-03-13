'''
# File 			: checkRail.py
# Description 	: Run "bio factory" command on the set of devices.
# Dependencies  : Unix OS(Linux or MAC), Python 2.7, pip, pexpect module (You can install it by running command "pip install pexpect")
				: Your boson login and password required to replace XXX.
# How to Run    : Run command "python checkRail.py"
# Output		: It will display output of "bio factory" command. The devices which are not connected to boson 
				: or bamio isn't available then it will log those devices with status in "checkRail.txt" file.
# Warning Note  : This script would not run on Windows.
'''

import pexpect
#import sys

Humidity_soak_samples = ['CC04B4001232','CC04B400122D']
Life_cycle_testing_samples = ['CC04B4001225','CC04B4001223','CC04B4001238','CC04B4001231','CC04B4001203','CC04B4001237','CC04B4001206','CC04B4001218']

#fread = open('deviceList.txt', 'r')
fwrite = open('checkRail.txt', 'w')
fread = ['CC04B4001232','CC04B400122D']

child = pexpect.spawn('ssh -p 6022 XXX@boson.bamlabs.com')			# enter your boson login
child.maxread=1000
i = child.expect(['hello','password: ','(yes/no)? '])
if i==0:
	print "Got yes/no?"
	child.sendline('yes')
	child.expect('password: ')

child.sendline('XXX')												# enter your boson password

count = 0
for line in fread:
	print "--------------------------------------------------"
	count=count+1
	deviceID = line.lower().replace('\n','')						# Assumed each line contains deviceID only
	deviceID = deviceID.replace(' ','')
	print "Device No."+str(count) + " Id: "+deviceID
	child.expect('$')
	child.sendline('bamssh '+ deviceID)

	child.expect('devid '+deviceID)
	child.expect([' found','port '])
	if child.before[-3:]=='not':
			print "Not connected to boson"
			fwrite.write(deviceID+'    : Not connected to boson\n')
			child.expect('$')
			continue

	i=0
	i = child.expect(['password: ','(yes/no)? '])
	if(i==1):
		if(child.before[-1]!= "s"):
			child.sendline('yes')

	child.expect('password: ')
	child.sendline('bam!ssh')
	child.expect('~# ')

	try:
		child.sendline('bio factory')								# Run "bio factory" command
		child.readline()
		for i in range(0,14):
			print child.readline(),
		child.sendline(' ')
		child.expect('~# ')											# Wait to complete execution of above command

	except:
		#print("Unexpected error:", sys.exc_info()[0])
		child.expect('~# ')
		print "bamio isn't available"
		fwrite.write(deviceID+"    : bamio isn't available\n")
		child.sendline('exit')
		child.expect('closed.')
		child.sendline(' ')
		child.expect('$')
		continue

	child.sendline('exit')											# Exit from current device
	child.expect('closed.')
	child.sendline(' ')
	child.expect('$')

print "--------------------------------------------------"

#fread.close()
fwrite.close()

child.sendline(' ')
child.expect('$')
child.sendline('exit')
child.kill(0)
print "Done"
exit(1)
