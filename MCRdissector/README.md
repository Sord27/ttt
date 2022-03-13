# MCRdissector


First off, you’ll need a Wireshark version that supports Lua 5.2. As I recall, Wireshark 1.12 doesn’t have the directory we need to place the dissector file. 

The installer for Wireshark 2.6 is in the EE HQ Teams, directory root/4. Admin / Installers – Dev Tools / Protocol Analyzer and Sniffers.

As you can see, the sn802.lua dissector file is also in this directory. The attached file and the one on Teams are the same.

The lua file is also under [source control](https://github.com/bam-labs/bamtools/tree/master/MCRdissector) on GitHub.

After you do that, place the sn802.lua file into this directory: C:\Program Files\Wireshark\plugins\2.6 

From there, boot up Wireshark and the Kinetis Protocol Analyzer and you should be good to go!


## Requirements
- [NXP Kinetis\_Protocol\_Analyzer\_Adapter.exe](https://www.nxp.com/webapp/Download?colCode=KINETIS-PRTCL-ANALYZER-ADAPTER&appType=license). This is a Windows adapter to interface multiple USB-KW41Z for sniffing multiple channels with wireshark. Only available on Windows as of 2/11/2019. One sniffer per channel required. SN currently uses 4 channels (11, 15, 20, 26). 
- [Wireshark 2.6](https://www.wireshark.org/download.html) Do not install the USBPcap library as part of this install, as it can cause issues.


## Support
- [USB-KW41Z NXP Page](https://www.nxp.com/products/processors-and-microcontrollers/arm-based-processors-and-mcus/kinetis-cortex-m-mcus/w-serieswireless-conn.m0-plus-m4/bluetooth-low-energy-ieee-802.15.4-packet-sniffer-usb-dongle:USB-KW41Z)
- [Teams Protocol Analyzer & Sniffer](https://teams.microsoft.com/_#/files/General?threadId=19%3A1cf6eae7cd0848cd889b820eefa5c2b5%40thread.skype&ctx=channel&context=4.%2520Admin%252FInstallers%2520-%2520Dev%2520Tools%252FProtocol%2520Analyzer%2520%2526%2520Sniffers)