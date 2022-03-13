
import logging
import re
import string


testserver =b' cat /bam/etc/bam.conf \r\nblohURL\t= https://svcsleepiq.sleepnumber.com:443\r\nblohConnectPath = /bam/requestConnection\r\nblohUplinkPath = /bam/uplink\r\nblohDownlinkPath = /bam/downlink\r\napplicationURL\t= https://svcsleepiq.sleepnumber.com:443/bam/data/processRawData.jsp\r\nprovisionURL    = https://svcsleepiq.sleepnumber.com:443/bam/device/getSoftware.jsp\r\nkeyURL\t\t\t\t\t= https://svcsleepiq.sleepnumber.com:443/bam/device/getFile.jsp\r\ntimeURL\t\t\t\t\t= https://svcsleepiq.sleepnumber.com:443/bam/device/getTime.jsp\r\nsyslogServer\t\t= devices_log.bamlabs.com\r\nsyslogFacility\t= local1\r\nvpnServer\t\t\t\t= devices_vpn.bamlabs.com\r\ntunnelURL\t\t\t\t=devices.zepp.bamlabs.com\r\nbam-conf=https://svcsleepiq.sleepnumber.com/bam/device/getConfig.jsp\r\nbam-prep=https://svcsleepiq.sleepnumber.com/bam/device/getSoftware.jsp\r\n\r\n#\r\n#report period is seconds\r\n#How often to send to the server in secs\r\n#\r\na2d_report_period = 1\r\n\r\n#\r\n# bam user land stuff\r\n# this may not be needed\r\n#\r\n# net_iface = rausb0\r\n# mac_addr = 00:12:0E:11:22:33\r\n# shm_size = 0x40000\r\n# mmap_size = 0x1000000\r\n#\r\n\r\n#Number of 1k samples per packet\r\n#0 - no 1k packets will be sent\r\n#10000 1k packet every 10 seconds\r\nusb_raw_send = 10000\r\n\r\n#Controls if we send 100hz data to the server.\r\nusb_filter_send = 0\r\n\r\n#Controls compression algorithem\r\nuse_dfcomp_a2d =1\r\n\r\n#Software\r\napplicationVersion = SE_500_zep4_4.0.7_1703141309_GA\r\nrfsVersion = SE_500_rfs_9.0.7-linaro_GA\r\n\r\n#Filters\r\n#lp = low pass, nt = notch\r\nfilter_lp20 = enable\r\nfilter_nt50 = disabled\r\nfilter_nt60 = disabled\r\n\r\n#WIFI SSID list\r\n#No spaces between\r\nuseOpenWifi=0\r\nuseHiddenSSID=1\r\n\r\n#ssids: [DADC96] \r\n\r\nbam-wpa=2MjP0uCpr7amtqOnpK305b2tv+G9pb/9pKS0iaStqaq3tb6/sZTrgZeWibmOhp2PmYqMjYqvloCcgYXLmZ2Nnp6K95+PX3JhYmo4Nw1uaHl/U39rbmVlei4lH3N2aHZ2RGp4bGxJTkweFS8sLUZMXlxDX0USSzs7Q0ZcWUVRTUMGCTc3TDMoJn5mAQcDC3B8aUZEPjw7bHBgHGdnY2EOHGtub2gcQmtrEAcECDgbGgMPUVxkEnp7HBYAAhkFE0QBcXUNDBbv8+v3/bizjYH6+eLosKzL0dXRqqK3nJ7z/OPE8frz653v7e3hr6/Qzdn1wMnUnpKSgvqBhYGP4P6JiImK/py1yaC3t6yap6uv9JmDjZ+Li9rYobC1u4mkq7C+5u3Xo9U=\r\nroot@500-cc04b401b576'
testserver = testserver.decode()
#print(testserver)
fndversionobj = re.search(r'(^blohURL\s=\shttps://)(.*?)(\.)',testserver, re.M)
print(fndversionobj.group(1))
print(fndversionobj.group(2))
print(fndversionobj.group(3))


'''
line = "Cats are smarter than dogs"

matchObj = re.match( r'(.*) are (.*?) .*', line, re.M|re.I)

if matchObj:
   print("matchObj.group() : ", matchObj.group())
   print("matchObj.group(1) : ", matchObj.group(1))
   print("matchObj.group(2) : ", matchObj.group(2)
else:
   print "No match!!"
'''
test = "<0x02035014>"

test = b' bio plgg ; bio mfvr ; baml\r\nlogging<errors & info>\r\nFND version<0x02035014>\r\nbaml [<level> [<expiration>]]\r\n  <level> is an integer >= 0; 0 turns logging off except for errors\r\n  <expiration> is a date string passed to touch via its -d option\r\n\r\nnow<2017-04-19 18:46:17>\r\n  log level<1> expires<2017-05-16 08:41:00>\r\nroot@500-64dba000005a'
test = test.decode()
print(test)

fndversionobj = re.search(r'(^FND version<)(0x[0-9A-Za-z]{8})(>\r$)', test, re.M)
if fndversionobj != None:
    version = fndversionobj.group(2)
    print(fndversionobj.group(2))
    #to do writ to to file
else:
    version = "N"
    print("error no version found")

fndversionobj = re.search(r'(^\s\slog\slevel<)(\d)(>)', test, re.M)
if fndversionobj != None:
    Logevel = fndversionobj.group(2)
    print("\n" + fndversionobj.group(2))
else:
    #to enbale the login level
    print("hjk")
'''
print("\n0")
print(fndversionobj.group(0))
print("\n1")
print(fndversionobj.group(1))
print("\n2")
print(fndversionobj.group(2))
print("\n3")
print(fndversionobj.group(3))



b' bio plgg ; bio mfvr ; baml\r\nlogging<errors & info>\r\nFND version<0x02035014>\r\nbaml [<level> [<expiration>]]\r\n  <level> is an integer >= 0; 0 turns logging off except for errors\r\n  <expiration> is a date string passed to touch via its -d option\r\n\r\nnow<2017-04-19 18:46:17>\r\n  log level<1> expires<2017-05-16 08:41:00>\r\nroot@500-64dba000005a'
'''
'''
cat /bam/etc/bam.conf
blohURL	= https://circle2-dg.circle.siq.sleepnumber.com
blohConnectPath = /bam/requestConnection
blohUplinkPath = /bam/uplink
blohDownlinkPath = /bam/downlink
applicationURL	= https://circle2-dg.circle.siq.sleepnumber.com/bam/data/processRawData.jsp
provisionURL    = https://circle2-dg.circle.siq.sleepnumber.com/bam/device/getSoftware.jsp
keyURL					= https://circle2-dg.circle.siq.sleepnumber.com/bam/device/getFile.jsp
timeURL					= https://circle2-dg.circle.siq.sleepnumber.com/bam/device/getTime.jsp
syslogServer		= devices_log.bamlabs.com
syslogFacility	= local1
vpnServer				= devices_vpn.bamlabs.com
tunnelURL				=devices.zepp.bamlabs.com
bam-conf=http://circle2-dg.circle.siq.sleepnumber.com/bam/device/getConfig.jsp
bam-prep=https://circle2-dg.circle.siq.sleepnumber.com/bam/device/getSoftware.jsp

#
#report period is seconds
#How often to send to the server in secs
#
a2d_report_period = 1

#
# bam user land stuff
# this may not be needed
#
# net_iface = rausb0
# mac_addr = 00:12:0E:11:22:33
# shm_size = 0x40000
# mmap_size = 0x1000000
#

#Number of 1k samples per packet
#0 - no 1k packets will be sent
#10000 1k packet every 10 seconds
usb_raw_send = 10000

#Controls if we send 100hz data to the server.
usb_filter_send = 0

#Controls compression algorithem
use_dfcomp_a2d =1

#Software
applicationVersion = SE_500_zep4_4.1.1_1704200801_GA
rfsVersion = SE_500_rfs_9.1.1-linaro_GA

#Filters
#lp = low pass, nt = notch
filter_lp20 = enable
filter_nt50 = disabled
filter_nt60 = disabled

#WIFI SSID list
#No spaces between
useOpenWifi=0
useHiddenSSID=1

#ssids: [Bug's Wi-Fi Network]

bam-wpa=2MjP0uCpr7amtqOnpK305b2tv+G9pb/9pKS0iaStqaq3tb6/sZTrgZeWibmOhp2PmYqMjYqvloCcgYXLmZ2Nnp6K95+PX3JhYmo4Nw1uaHl/U39rbmVlei4lH3N2aHZ2RGp4bGxJTkweFS8sLUZMXlxDX0USSzs7Q0ZcWUVRTUMGCTc3TDMoJn5mBzMgbzpqHCVgCCZwHzcnIzokPHpTUysvNmN9AQsyUVRVUFdRSEhhZR4NDh4uAQAdEUtGcgRw
root@500-64dba0000228:~#


b' cd /bam/firmware; ls\r\nble-firmware-00010404.bin       foundation-device-0203500D.bin\r\nble-firmware-00020204.bin       smart-pump-01045005.bin\r\nble-firmware-00030105.bin       smart-pump-02035005.bin\r\nble-firmware-00040104.bin       smart-pump-03025005.bin\r\nfoundation-device-02015000.bin  smart-pump-04015006.bin\r\nroot@500-cc04b401b576:/bam/'

'''