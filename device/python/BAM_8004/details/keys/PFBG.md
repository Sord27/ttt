Returns a bit mask as a hex number, e.g. `"08000000E"` that indicates what software features are compiled into the
current software. This bits are interpreted as shown in the following table.

| Value | Description |
| --- | --------------- |
| `0x00000001` | Has a shell |
| `0x00000002` | Uses ADC |
| `0x00000004` | Has BLE |
| `0x00000008` | Has LEDs |
| `0x00000010` | Uses the Thump Pump |
| `0x00000020` | Has FWS. Uses the BAM I/O-based, instead of the MCR-based, firmware server |
| `0x80000000` | Supports SP2 |