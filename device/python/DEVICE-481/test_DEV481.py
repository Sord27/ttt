import time
import random
import subprocess
import array

print('DEV481 test start')
var = 1
#Reboot between extend and retract
#1 = reboot, 0 = no reboot
REBOOT = 0
#Add random sleep at the end
#1 = random time, 0 = disable 
RANDOMIZE = 1
#defult sleep for move
SLEEPY_TIME = 40
#print Debugging info 
DEBUG = 0 
#Variable
command = "bio MFST"
output = "test"
failed = 0
success = 0
toggle = 0
RH_BYTE_POS = 20
Actuators = ["Right Head","Left Head","Right Foot","Left Foot"]
#Create Over Current Array
Act_Over_Curr = array.array('i',(0 for i in range(0,4)))
#Create No Motion Array
Act_No_Motion = array.array('i',(0 for i in range(0,4)))
with open("DEVICE481.out","w+") as f:
        f.write("The number of times homing failed:            \n")
        f.write("The number of successful runs:            \n")
        f.write("Over Current Errors: \n Right Head     Left Head     \n Right Foot     Left Foot     \n")
        f.write("No Motion Errors: \n Right Head     Left Head     \n Right Foot     Left Foot     \n")
while var == 1:
#Toggle Between Right and Left sides 
        if toggle == 0:
                toggle = 1
                subprocess.call(["bio","MFUL","100","0"])
                time.sleep(SLEEPY_TIME)
                if REBOOT == 1:
                    subprocess.call(["bio","MFFU","2"])
                    time.sleep(5)
                subprocess.call(["bio","MFPL","40"])
        else:
                toggle = 0
                subprocess.call(["bio","MFFL","100","0"])
                time.sleep(SLEEPY_TIME)
                if REBOOT == 1:
                    subprocess.call(["bio","MFFU","2"])
                    time.sleep(5)
                subprocess.call(["bio","MFPR","40"])
        time.sleep(SLEEPY_TIME)
        command = ['bio', 'MFST']
        CommandBuffer = subprocess.Popen(command, stdout=subprocess.PIPE)
        output = CommandBuffer.stdout.read()
        if "Foundation needs homing" in output:
            for x in range (4):
                if Actuators[x] + " motor over current" in output:
                    Act_Over_Curr[x] = Act_Over_Curr[x] + 1
                    with open("DEVICE481.out","r+b") as f:
                        content = f.read()
                        f.seek(content.index(Actuators[x])+12)
                        f.write(str(Act_Over_Curr[x]))
                Actuator_bin = output[(output.index(')<')+(RH_BYTE_POS+x*2)):(output.index(')<')+(RH_BYTE_POS+2+x*2))]
                if Actuator_bin == "20":
                    Act_No_Motion[x] = Act_No_Motion[x] + 1
                    with open("DEVICE481.out","r+b") as f:
                        content = f.read()
                        f.seek(content.index(Actuators[x],(content.index(Actuators[x])+1))+12)
                        f.write(str(Act_No_Motion[x]))
        command = ['bio', 'MFST']
        CommandBuffer = subprocess.Popen(command, stdout=subprocess.PIPE)
        output = CommandBuffer.stdout.read()
        if "Foundation needs homing" in output:
                failed = failed + 1
                if DEBUG == 1:
                    print "Homing Failed \n", output
                with open("DEVICE481.out","r+b") as f:
                        content = f.read()
                        f.seek(content.index('d:')+5)
                        f.write(str(failed))
                subprocess.call(["bio","MFPL","1280"])
                #homing runs at half speed so it takes longer to complete
                time.sleep(SLEEPY_TIME*1.5)
        else:
                success = success + 1
                with open("DEVICE481.out","r+b") as f:
                        content = f.read()
                        f.seek(content.index('s:')+5)
                        f.write(str(success))
        if RANDOMIZE == 1:
            time.sleep(5+random.randint(1,10))