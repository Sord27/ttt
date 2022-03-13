
import logging
import re
import string






test = b' cd /bam/firmware; ls\r\nble-firmware-00010404.bin       foundation-device-0203500D.bin\r\nble-firmware-00020204.bin       smart-pump-01045005.bin\r\nble-firmware-00030105.bin       smart-pump-02035005.bin\r\nble-firmware-00040104.bin       smart-pump-03025005.bin\r\nfoundation-device-02015000.bin  smart-pump-04015006.bin\r\nroot@500-cc04b401b576:/bam/'
test = test.decode()
print(test)

fndversionobj = re.search(r'(foundation-device-)([0-9A-Za-z]{3}35[0-9A-Za-z]{3})(\.bin\r\n)', test, re.M)
if fndversionobj != None:
    print("\n0")
    print(fndversionobj.group(0))
    print("\n1")
    print(fndversionobj.group(1))
    print("\n2")
    print(fndversionobj.group(2))
    FND = "0x" + fndversionobj.group(2)

    print("\n3")
    print(fndversionobj.group(3))
    version = fndversionobj.group(2)
    print(fndversionobj.group(2))
    #to do writ to to file
else:
    version = "N"
    print("error no version found")

print("\n")
print(FND)







'''
b' cd /bam/firmware; ls\r\nble-firmware-00010404.bin       foundation-device-0203500D.bin\r\nble-firmware-00020204.bin       smart-pump-01045005.bin\r\nble-firmware-00030105.bin       smart-pump-02035005.bin\r\nble-firmware-00040104.bin       smart-pump-03025005.bin\r\nfoundation-device-02015000.bin  smart-pump-04015006.bin\r\nroot@500-cc04b401b576:/bam/'

'''