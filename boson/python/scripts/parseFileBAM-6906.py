'''
# File 			: parseFileBAM-6906.py
# Description 	: To parse unique sorted device list from given input file.
# Dependencies  : python2.7
# How to Run    : Run command "python parseFileBAM-6906.py"
# Input 		: Run command on boson : cat /var/log/bamlog | grep A:USB_MGR >pbwg.out
				: Copy file "pbwg.out" to local machine on which you want to parse data.
# Output		: This script will display parsed device Ids in sorted order and save results to a file.
'''

fread = open('Jul 31 - Aug 2_3_30pm bamlog.txt', 'r')
fwrite = open('Fetched devices from Jul 31 - Aug 2_3_30pm bamlog.txt', 'w')
count = 0
list1 = []
for line in fread:
	str1 = line.split(' ')
	if(str1[5][:3]!='500'):
		continue
	device = str1[5]
	#if device not in deviceList:
	list1 += [device]
	#print device
	count = count + 1
	#if count>100:
	#	break

fread.close()

print 'Done'
print len(list1)   
list2 = list(set(list1))    
list2.sort(key=list1.index)
list2 = sorted(list2)
print len(list2)    
for i in list2:
	fwrite.write(i+'\n')
	print i

fwrite.close()
#print sorted(list2)