Changes the configuration used by the hardware by sending a 4-digit hex number, e.g. `"0002"`

| Value | Description |
| ---- | ---- |
| `0x0001` | Single Chamber (clear when dual chamber is used) |
| `0x0002` | Wedge is present (clear when there is no wedge) |
| `0x0004` | Kids chamber is used (clear when adult chamber type is used)

This is used for testing and debugging purposes