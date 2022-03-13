Gets the current status of the Responsive Air system. Will return an 11 byte number formatted according to the following tables.

# Byte 0: Left/Right Enable #

Gets the status of the Responsive Air system

| Value | Description |
| ---- | ---- |
| 0 | Both sides disabled |
| 1 | Only right side enabled |
| 2 | Only left side enabled |
| 3 | Both sides enabled |


# Bytes 1-4: Poll Frequency #

Seconds between each check to see if an adjustment should happen.

This will be between 60 and 1728000.

__Default:__ 300


# Bytes 5-6: In Bed Timeout #

Seconds in bed before an initial adjustment happens.

This will be between 0 and 3600.

__Default:__ 20


# Bytes 7-10: Out of bed Timeout #

Seconds out of bed before the final adjustment happends.

This will be between 0 and 172800.

__Default:__ 1800


# Byte 11: Adjustment Threshold #

Steps of 5 that the measured sleep number can be off before an adjustment happens.

This will be between 0 and 20.

__Default:__ 20
