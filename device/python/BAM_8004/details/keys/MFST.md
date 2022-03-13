Returns information about the foundation in a series of 15 contiguous, 
undifferentiated hex bytes. 

e.g. `“420000000000000000000000004400”`.

| Hex Byte | Description | Values |
| --- | --- | --- |
| 0	| Configuration	| See table below |
| 1	| Right head position | Between 0 and 100 |
| 2	| Left head position | Between 0 and 100 |
| 3	| Right foot position | Between 0 and 100 |
| 4	| Left foot position | Between 0 and 100 |
| 5-6 | Right position timer | Minutes up to 180. LSB order |
| 7-8 | Left position timer	Minutes up to 180. LSB order |
| 9	| Left head motor status | See motor status table |
| 10 | Right head motor status | See motor status table |
| 11 | Left foot motor status | See motor status table |
| 12 | Right foot motor status | See motor status table |
| 13 | Timer Preset | See preset table |
| 14 | Current Preset | See preset table |

# Configuration Byte #

`<7><6><5><4><3><2><1><0>`

| Bit | Definition | 
| ---- | ---- |
| 7 | Always 0 |
| 6 | Foundation Configured |
| 5 | Foundation needs homing |
| 4 | Outlets have non-zero timer |
| 3 | One or more outlets are on |
| 2,1 | Foundation Configuration: |
| | 0 - Single Foundation |
| | 1 - Split Head Foundation |
| | 2 - Split King Foundation |
| | 3 - Eastern King Foundation |
| 0 | Foundation is moving |

# Motor Status #

| Value | Definition |
| ---- | ---- |
| `0x01` | Actuator is moving |
| `0x02` | Flat limit switch is true |
| `0x04` | High limit switch is true |
| `0x08` | Motor over-temp |
| `0x10` | Motor over-current |

# Preset #

High nibble is left preset and low nibble is right preset

| Value | Preset |
| ---- | ---- |
| 0 | None |
| 1 | Custom |
| 2 | Reading |
| 3 | Watch TV |
| 4 | Flat |
| 5 | Zero-G |
| 6 | Snore |

