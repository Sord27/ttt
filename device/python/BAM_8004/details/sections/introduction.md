# Introduction #

This document describes the keys that can be used on the Sleep Expert for use in controlling and querying the system. 
A key can either be a setter or a getter. Getters are used for retrieving some data from some part of the system. 
Getters can not have arguments. Setters can have an associated argument with the key, but this is not mandatory. 
A setter will not return any output. 


## System Components ##

<div id="architecture">
![Platform Architecture]( details/images/architecture.pdf ){ width=80% }

</div>

### Sleep Expert ###

Sleep Expert is a Linux system which is connected to the internet allowing for communication between the Smart Pump 
and the cloud.

### Smart Pump ###

The smart pump is responsible for communicating with peripherals using Bluetooth Low Energy, 802.15.4, and CAN as well
as controlling the pump and reading the pressure sensor. The Smart Pump is running 
[MQX RTOS](https://www.nxp.com/pages/mqx-real-time-operating-system-rtos:MQXRTOS) which allows for very fast response
times for user generated events such as changning the Sleep Number via the Remote or Smart Phone Applications, or
keeping their Sleep Number steady using Responsive Air. 

## Communication ##

There are many different communication protocols used in the Pump.

### MCR (802.15.4) ###

The MCR communication protocol is using the [IEEE 802.15.4](https://en.wikipedia.org/wiki/IEEE_802.15.4) standard for 
communcication between the pump and various accessories. 

### Bluetooth Low Energy (BLE) ###

Bluetooth Low Energy is used communicating with smart phone applications. 

### CAN Bus ###

CAN is used for communication between the Smart Pump and the Foundation.


### USB ###

USB is used for connecting the Smart Pump and Sleep Expert, as well as various peripherals. The audio input for the 
snore functionality comes from a USB ADC and the Sleep Expert can use Ethernet rather than WiFi by plugging in a
USB ethernet adapter. 


### BLOH ###

This is the communication protocol used to communicate with the server 


## Hardware Versions ##

Bammit and the BAMKeys are on multiple Sleep Number pumps. 

### Pumps ###

#### SP1 ####

First generation pump with SleepIQ technology

#### SP2 ####

Second generation pump with SleepIQ technology

#### SP3 ####

Cost reduction model of SP1 pump.

#### Genie ####

Low cost, pump-less smart bed with SleepIQ technology.

#### SP 360 ####

The first device that puts both the Sleep Expert and the Smart Pump on the same printed circuit board.


### Remotes ###

#### 360 ####

#### Legacy ####

### Foundations ###

#### 360 ####

#### Legacy ####

### Dual-temp ###

#### Marlow ####

Legacy version of Dual-temp

#### Gentherm ####

The newest version of Dual-Temp