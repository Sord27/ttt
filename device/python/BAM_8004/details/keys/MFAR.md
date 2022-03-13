This command performs foundation position, speed, and/or massage state changes for the right side of the foundation. 
It is a complex command that takes 10 parameters in a contiguous, undifferentiated string of hex digits, 
e.g. `“3500FFFFFFFFFF5A00FFFFFF”`. Use `0xFF` or `0xFFFF` to ignore any parameter you don’t want affected.

| Digit | Description | Value |
| ---- | ---- | ---- |
| 0	| Head position | Between 0 and 100 |
| 1	| Speed of head change | 0 - Fast | 
| | | 1 - Slow |
| 2	| Foot position | Between 0 and 100 |
| 3	| Speed of foot change | 0 - Fast |
| | | 1 - Slow |
| 4	| Head massage setting | Between 0 and 3 |
| 5	| Foot massage setting | Between 0 and 3 |
| 6	| Wave massage setting | Between 0 and 3 |
| 7-8 |	Foundation Timer in minutes (LSB) |Between 0 and 180 |
| 9	| Preset | 1 - Custom |
| | | 2 - Reading |
| | | 3 - Watching TV |
| | | 4 - Flat | 
| | | 5 - Zero-G | 
| | | 6 - Snore |
| 10-11	| Massage timer in minutes (LSB) | Between 0 and 180 |

 