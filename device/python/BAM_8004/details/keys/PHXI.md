Returns the current status of the internally selected operations.
Bit mask is returned as a hex number, e.g. `"0x00000000"`.
The possible bit values are:

| Value | Definition | Description |
| ---- | ----- | ----------------- |
| `0x00000001` | Target is Widened | When Set, a wider acceptable real SSN will be accepted when changed the Sleep Number setting. This allows smaller test chambers to pass more tests as they are harder to pump to the exact Sleep Number setting |
| `0x00000002` | Extend Pump Status | When set, an extended frame is sent to the server. Older systems cannot handle the extended frame, so this bit is turned on once the system capability has been verified |


