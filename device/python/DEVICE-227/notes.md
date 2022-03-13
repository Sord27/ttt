# Raw data packet structure #

This document is created using source code from `RawDataPacket.java` in Spyder-1.


## Java primative types ##

* **byte**: The byte data type is an 8-bit signed two's complement integer. It has a minimum value of -128 and a maximum value of 127 (inclusive). The byte data type can be useful for saving memory in large arrays, where the memory savings actually matters. They can also be used in place of int where their limits help to clarify your code; the fact that a variable's range is limited can serve as a form of documentation.
* **short**: The short data type is a 16-bit signed two's complement integer. It has a minimum value of -32,768 and a maximum value of 32,767 (inclusive). As with byte, the same guidelines apply: you can use a short to save memory in large arrays, in situations where the memory savings actually matters.
* **int**: By default, the int data type is a 32-bit signed two's complement integer, which has a minimum value of -231 and a maximum value of 231-1. In Java SE 8 and later, you can use the int data type to represent an unsigned 32-bit integer, which has a minimum value of 0 and a maximum value of 232-1. Use the Integer class to use int data type as an unsigned integer. See the section The Number Classes for more information. Static methods like compareUnsigned, divideUnsigned etc have been added to the Integer class to support the arithmetic operations for unsigned integers.
* **long**: The long data type is a 64-bit two's complement integer. The signed long has a minimum value of -263 and a maximum value of 263-1. In Java SE 8 and later, you can use the long data type to represent an unsigned 64-bit long, which has a minimum value of 0 and a maximum value of 264-1. Use this data type when you need a range of values wider than those provided by int. The Long class also contains methods like compareUnsigned, divideUnsigned etc to support arithmetic operations for unsigned long.
* **float**: The float data type is a single-precision 32-bit IEEE 754 floating point. Its range of values is beyond the scope of this discussion, but is specified in the Floating-Point Types, Formats, and Values section of the Java Language Specification. As with the recommendations for byte and short, use a float (instead of double) if you need to save memory in large arrays of floating point numbers. This data type should never be used for precise values, such as currency. For that, you will need to use the java.math.BigDecimal class instead. Numbers and Strings covers BigDecimal and other useful classes provided by the Java platform.
* **double**: The double data type is a double-precision 64-bit IEEE 754 floating point. Its range of values is beyond the scope of this discussion, but is specified in the Floating-Point Types, Formats, and Values section of the Java Language Specification. For decimal values, this data type is generally the default choice. As mentioned above, this data type should never be used for precise values, such as currency.
* **boolean**: The boolean data type has only two possible values: true and false. Use this data type for simple flags that track true/false conditions. This data type represents one bit of information, but its "size" isn't something that's precisely defined.
* **char**: The char data type is a single 16-bit Unicode character. It has a minimum value of `\u0000` (or 0) and a maximum value of `\uffff` (or 65,535 inclusive).


## Header ##

| Value | Type | Bytes |
| --- | --- | --- |
| Version | short | 2 |
| none | short | 2 |
| tagid | short | 2 |
| tag length (bytes) | short | 2 |
| Device ID | long | 8 |
| tagid | short | 2 |
| tag length (bytes) | short | 2 |
| A2D channels | int | 4 |
| tagid | short | 2 |
| tag length (bytes) | short | 2 |
| A2D sampling rate | int | 4 |
| tagid | short | 2 |
| tag length (bytes) | short | 2 |
| Time Zone | string | not explicitly defined |
| tagid | short | 2 |
| tag length (bytes) | short | 2 |
| Hardware Version | int | 4 |
| tagid | short | 2 |
| tag length (bytes) | short | 2 |
| Device Configuration | int | 4 |


## v2 Packets ##

```java
public void writeV2(DataOutput dataOut) throws IOException {
    writeHeader(dataOut);

    // Timestamp
    TagUtils.writeTagLong(dataOut, TAG_GMT_TIME, getTimeStamp());

    int numberOfSamples = getNumberOfSamples();
    dataOut.writeShort(TAG_XPORT_DATA_USB_RAW);
    dataOut.writeShort(numberOfSamples * 4 + 4); // in bytes

    dataOut.writeByte(0); // dev id
    dataOut.writeByte(0); // sub id
    dataOut.writeByte(FxDevice.PAD_SENSOR); // option 1
    dataOut.writeByte(0); // option 2

    dataOut.writeInt(9999); // Serial
    dataOut.writeInt(getSeqNumber()); // Seq number

    dataOut.writeShort(getSamplingPeriod());
    dataOut.writeShort(getNumberOfSamples());
    dataOut.writeLong(getTimeStamp());

    int[] channelData = getChannelData(0);
    for (int i = 0; i < numberOfSamples; i++) {
        dataOut.writeInt(channelData[i]);
    }

    TagUtils.padData(dataOut, numberOfSamples * 4 + 4);

    // Write Accel Data
    int accelXYZ[] = getAccelXYZ();
    if (accelXYZ != null) {
        TagUtils.writeTag(dataOut, TAG_ACCEL_XYZ, accelXYZ);
    }

    // Write Strap
    int strapData[] = getStrapData();
    if (strapData != null) {
        TagUtils.writeTag(dataOut, TAG_RAW_STRAP_HR, strapData);
    }

    // Write sync pulse if any
    SyncPulseDataPoint synchData[] = getSyncPulseDataPoints();
    if (synchData != null) {
        dataOut.writeShort(TAG_D2A_CHICKEN_HEART);
        dataOut.writeShort(synchData.length * SYNC_PULSE_STRUCT_SIZE); // In bytes
        for (int i = 0; i < synchData.length; i++) {
            dataOut.writeLong(synchData[i].getTimeGMT());
            dataOut.writeInt(synchData[i].getValue());
            dataOut.writeInt(0); // Write dummy int
        }
        TagUtils.padData(dataOut, synchData.length * SYNC_PULSE_STRUCT_SIZE);
    }

    // Write Commands if any
    if (m_deviceCommand != -1) {
        TagUtils.writeTagInt(dataOut, TAG_DEVICE_COMMAND, m_deviceCommand);
    }

    // wifi stats from kernel
    TagUtils.writeTag(dataOut, TAG_IW_STATS_QUAL, getWifiQual());

    // Write Test Tags
    if (getDontStoreDataInDB()) {
        TagUtils.writeTag(dataOut, TAG_TEST_DONT_STORE_DATA_IN_DB);
    }

    if (getDontStoreDataInFile()) {
        TagUtils.writeTag(dataOut, TAG_TEST_DONT_STORE_DATA_IN_FILE);
    }

    if (m_pumpStatus != 0 || m_foundationStatus != 0) {
        // Sensor Serial
        // MSB/LSB Pump Status
        // Right Sleep Number
        // Left Sleep Number

        dataOut.writeShort(TAG_PUMP_STATUS);
        dataOut.writeShort(4); // in bytes
        dataOut.writeInt(m_sensorSerialNumber);
        dataOut.writeByte(m_pumpStatus);
        dataOut.writeByte(m_foundationStatus);
        dataOut.writeByte(m_sleepNumber);
        dataOut.writeByte(0); // Reserved
        TagUtils.padData(dataOut, 4);
    }

    // Write if algo init happened
    if (getIsAlgoInit()) {
        TagUtils.writeTag(dataOut, TAG_ALGO_INIT);
    }

    // Always last tag in the header
    dataOut.writeShort(TAG_END_OF_LIST);
}
```
| Value | Type | Bytes |
| --- | --- | --- |
| tagid | short | 2 |
| tag length (bytes) | short | 2 |
| time stamp | long | 8 |
| XPORT_DATA | short | 2 |
| number of samples | short | 2 |
| dev id | byte | 1 |
| sub id | byte | 1 |
| pad sensor option 1 | byte | 1 |
| option 2 | byte | 1 |
| serial | int | 4 |
| seq number | int | 4 |
| sampling period | short | 2 |
| number of samples | short | 2 |
| long |  |  |


# Conversation with Kavita #

>**Alex Norell** [3:46 PM]
>Hey. I’m looking into how the raw1k file is generated and I’ve got a couple questions. Eric told me you might be the person to ask.
>I want to parse the raw1k file to get out pressure data and other events and I’m currently looking at the `bam-raw/src/main/java/com/bam/data/RawDataPacket.java` file. There seem to be two `write` functions. Which one should I look at, or am I even looking in the right place?

>**Kavita Kolli** [4:14 PM]
>not write, you ahve to check read methods ..
>but that is not it .. there is a layer on the top of it that reads a set of other tags ..

>**Alex Norell** [4:15 PM]
>I want to see how it is written, so that I can read it back

>**Kavita Kolli** [4:15 PM]
>ok..
>writeProcessedData is one method ..
>public void write(DataOutput dataOut)  is what writes most of the raw data related stuff . processed data is mainly dsp report + pump status etc
>what will you be using to parse this file .. r u going to write a script or program or !!

>**Alex Norell** [4:19 PM]
>Yeah. My plan was to write a python script or a C program that reads in the raw1k file and creates a data structure with all of the session events
>I will mostly be using the pressure data for simulating a pump though

>**Kavita Kolli** [4:19 PM]
>ok …

>**Alex Norell** [4:20 PM]
>Where is the initial call to start creating a raw1k file at?

>**Kavita Kolli** [4:20 PM]
>readProcessedData method will help you understand how it can be read ..

>**Alex Norell** [4:21 PM]
>Thank you!

>**Kavita Kolli** [4:21 PM]
>its in RawDataWriterWorker calls RawDataWriter (edited)
>to be clear its RawDataFile.writeData() line 340 .. -> calls RawDataFileAccessorV8 (inherits BaseRawDataFileAccessor) (edited)
>there is a concept of header for the file, that is the first thing written to file (it has some set of tags), followed by data from each RDP ..

>**Alex Norell** [4:25 PM]
>Awesome! I was wondering where the first couple dozen bytes came from. I can see where the `writeHeader()` function is called due to the TimeZone being in ASCII, but there were too many bytes before that to make sense.

>**Kavita Kolli** [4:25 PM]
>does this help !!

>**Alex Norell** [4:25 PM]
>Very much so. Thank you so much!

>**Kavita Kolli** [4:25 PM]
>sure ..

