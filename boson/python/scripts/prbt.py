import pexpect
import time

#deviceID = raw_input('Please enter device ID(last 5 digits): ')
fread = open('deviceList.txt', 'r')
fwrite = open('writeStatus_prbt_deviceList.txt', 'w')

child = pexpect.spawn('ssh -p 6022 XXX@boson.bamlabs.com')		# Replace XXX with your username
#child.maxread=1000
#print('Entered ssh')
i = child.expect(['hello','password: ','(yes/no)? '])
#print i
if i==0:
	print "Got yes/no?"
	child.sendline('yes')
	child.expect('password: ')

child.sendline('XXX')							# Replace XXX with your password
child.readline()
#print('sent password')

count = 0
for line in fread:
	print "--------------------------------------------------"
	count=count+1
	deviceID = line.lower().replace('\n','')			# Assumed each line contains deviceID only
	deviceID = deviceID.replace(' ','')
	print "Device No."+str(count) + " Id: "+deviceID
	child.expect('$')
	child.sendline('bamssh '+ deviceID)
	#print ('Entered bamssh')

	child.expect('devid '+deviceID)
	#print ('Got devid')
	child.expect([' found','port '])
	if child.before[-3:]=='not':
			print "Not connected to boson"
			fwrite.write(deviceID+'    : Not connected to boson\n')
			child.expect('$')
			continue
	#print ('Got port')
	i=0
	i = child.expect(['password: ','(yes/no)? '])
	#print child.before
	if(i==1):
		if(child.before[-1]!= "s"):
			child.sendline('yes')

	#print "Expecting for password for bamssh"
	child.expect('password: ')
	#print child.before
	child.sendline('bam!ssh')
	child.expect('~# ')

	try:
		child.sendline('bio prbt 0')
		child.expect('~# ')
		print "success"

	except:
		child.expect('~# ')
		print "bamio isn't available"
		fwrite.write(deviceID+"    : bamio isn't available\n")
		child.sendline('exit')
		child.expect('closed.')
		child.sendline(' ')
		child.expect('$')
		continue

	print 'exiting from current device'
	child.sendline('exit')
	child.expect('closed.')
	child.sendline(' ')
	child.expect('$')

fread.close()
fwrite.close()

child.sendline(' ')
child.expect('$')
child.sendline('exit')
child.kill(0)
print "Done"
exit(1)
#child.interact()				# Give control of the child to the user.
