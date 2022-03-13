'''
# File 			: checkFirmwareUpdateFromFile_BAM-6906.py
# Description 	: Check firmware versions by comparing output from 'bio MFWL' and 'bio PBVR/PVER' commands on given device,
				: if it's same then do nothing(Success) else log failure message to a file.
# Dependencies  : Unix OS(Linux or MAC), Python 2.7, pip, pexpect module (You can install it by running command "pip install pexpect")
				: Your boson login and password required to replace XXX.
# How to Run    : Run command "python checkFirmwareUpdateFromFile_BAM-6906.py"
# Output		: It will display k20/ble firmware versions and status(success/FAILURE) on the terminal and will log failure devices to a file "writeStatus.txt".
# Warning Note  : This script would not run on Windows.
'''

import pexpect
import time

fread = open('Fetched devices from Jul 31 - Aug 2_3_30pm bamlog.txt', 'r')
fwrite = open('writeStatus.txt', 'w')

child = pexpect.spawn('ssh -p 6022 XXX@boson.bamlabs.com')				# enter your boson login
#child.maxread=1000
i = child.expect(['hello','password: ','(yes/no)? '])
if i==0:
	print "Got yes/no?"
	child.sendline('yes')
	child.expect('password: ')

child.sendline('XXX')													# enter your boson password

count = 0
for line in fread:
	#try:
		print "--------------------------------------------------"
		count=count+1
		deviceID = line.split('-')
		deviceID = deviceID[1].replace(' ','')
		deviceID = deviceID.replace('\n','')
		print "Device No."+str(count) + " Id: "+deviceID	
		child.expect('$')
		child.sendline('bamssh '+ deviceID)
		child.expect('devid ')
		child.expect([' found','port '])
		if child.before[-3:]=='not':
			print "Not connected to boson"
			fwrite.write(deviceID+'    : Not connected to boson\n')
			child.expect('$')
			continue

		i=0
		i = child.expect(['password: ','(yes/no)? '])
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
				fwrite.write(deviceID+"    : bamio isn't available\n")
				child.sendline('exit')
				child.expect('closed.')
				child.sendline(' ')
				child.expect('$')
				continue
			
			child.expect('>')
			i = child.before			# No. of fw_images
			fw_image = i.split('<')
			fw_image = fw_image[1]

			valid_image = True

			if(fw_image=='2'):			# For GVB
				print fw_image

				child.expect('>')
				i = child.before		# gvb-ble
				ble = i.split('<')
				ble = ble[1]

				child.expect('>')
				i = child.before		# gvb-k20
				k20 = i.split('<')
				k20 = k20[1]

			elif (fw_image=='5'):		# For SP1/SP2
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

			else:
				valid_image = False
				child.expect('~# ')
				fwrite.write(deviceID+'    : Number of firmware images are not correct\n')
				print "Number of firmware images are not correct"

		except:
			print "Firmware List<[error]>"
			child.expect('~# ')
			fwrite.write(deviceID+'    : Firmware List error\n')
			child.sendline('exit')
			child.expect('closed.')
			child.sendline(' ')
			child.expect('$')
			continue

		try:
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

				print k20, actual_k20
				print ble, actual_ble
				
				if(k20==actual_k20 and ble==actual_ble):
					print "success"
				else:
					print "FAILURE!"
					fwrite.write(deviceID+'    : FAILURE\n')

					# Remove below comments if you want to reboot the pump
					'''
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

					print k20, actual_k20
					print ble, actual_ble
					if(k20==actual_k20 and ble==actual_ble):
						print "Updated firmware successfully!"
					else:
						print "FAILURE!"
						fwrite.write(deviceID+'    : FAILURE\n')
					'''

		except:
			print "Expect bio factory error"
			child.expect('~# ')
			fwrite.write(deviceID+'    : Expect bio factory error\n')
			child.sendline('exit')
			child.expect('closed.')
			child.sendline(' ')
			child.expect('$')
			continue
		
		child.sendline('exit')
		child.expect('closed.')
		child.sendline(' ')
		child.expect('$')
	#except:
		#print "Some exceptions generated!!"
	
fread.close()
fwrite.close()
child.sendline(' ')
child.expect('$')
child.sendline('exit')
child.kill(0)
exit(1)
