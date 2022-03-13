Returns a list of firmware images in the pump SPI flash list. This is returned as a contiguous, undifferentiated string of hex digits.

The first 2-digit byte indicates the total number of images that follow.

Each subsequent 14-byte string represents a loaded firmware file in the following format:

| Byte | Value |
| ---- | ---- |
| 0	| dev ID |
| 1	| sub ID |
| 2	| version: MAJOR |
| 3	| version: MINOR |
| 4	| version: PROTOCOL REV |
| 5	| version: DEV BUILD (0 for release) |
| 6-9 | CRC32 of firmware image |
| 10-13 | Size of image in bytes |

 