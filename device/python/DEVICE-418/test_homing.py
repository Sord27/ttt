import time
import random
import subprocess

print('homing test')
var = 1
command = ['bio', 'MFST']
output = "test"
failed = 0
success = 0
DELAY_TIME = 15
with open("homeTesting.out","w+") as f:
	f.write("The number of times homing failed:            \n")
	f.write("The number of successful runs:            \n")
while var == 1:
#Move all Actuators to increase chances of homing failures  
        subprocess.call(["bio","MFUL","50","0"])
        time.sleep(DELAY_TIME+random.randint(1,10))
	subprocess.call(["bio","MFUR","50","0"])
	time.sleep(DELAY_TIME+random.randint(1,10))
        subprocess.call(["bio","MFFL","50","0"])
        time.sleep(DELAY_TIME+random.randint(1,10))
        subprocess.call(["bio","MFFR","50","0"])
        time.sleep(DELAY_TIME+random.randint(1,10))
        subprocess.call(["bio","MFPL","1280"])
#	if homing is succesful it should only take half the time
	time.sleep(45)
	command = ['bio', 'MFST']
        CommandBuffer = subprocess.Popen(command, stdout=subprocess.PIPE)
        output = CommandBuffer.stdout.read()
#	add more time for homing timeout to happen
	if "Foundation needs homing" in output:
        	time.sleep(50)
#	if the homing is still needed, failure has happened, record and reset
        command = ['bio', 'MFST']
        CommandBuffer = subprocess.Popen(command, stdout=subprocess.PIPE)
        output = CommandBuffer.stdout.read()
        if "Foundation needs homing" in output:
                failed = failed + 1
               	with open("homeTesting.out","r+b") as f:
			content = f.read()
			f.seek(content.index('d:')+5)
			f.write(str(failed))		 
#		Use Underbed Light hard reset the foundation using a relay inline with power
		subprocess.call(["bio","MULR","1"])
		time.sleep(10)
		subprocess.call(["bio","MFPL","1280"])
	else: 
		success = success + 1
		with open("homeTesting.out","r+b") as f:
			content = f.read()
			f.seek(content.index('s:')+5)
			f.write(str(success))
		#soft reboot the foundation to help induce a failure on next cycle 
        	subprocess.call(["bio","MFFU","2"])
        	time.sleep(5+random.randint(1,5))
        time.sleep(5)
