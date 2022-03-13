This returns a string of contiguous, undifferentiated hex characters that provide various data regarding the pump.

| Byte | Description | Value | Definition
| ---- | ---- | ---- | ---- | 
| 1 | Number of chambers | 0 | Single |
| |	| 1 | Dual |
|2 | Task in progress | 0 | Nothing running |
| | | 1 | Task running |
| | | 2	| Task pending |
| 3	| Right side Sleep Number | | |	 	 
| 4	| Left side Sleep Number | | | 	 

