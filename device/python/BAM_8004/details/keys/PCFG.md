This returns two 4-digit hex numbers, separated by a dash. e.g. `"0006-0002"`

The first number is the default configuration as determined by the hardware. The second - used internally - is initially set to the same value, but may be changed by the Set Configuration([PCFS](#PCFS)) command for testing and debugging purposes. The bits are interpreted as:

| Value | Description |
| ---- | ---- |
| `0x0001` | Single Chamber (clear when dual chamber is used) |
| `0x0002` | Wedge is present (clear when there is no wedge) |
| `0x0004` | Kids chamber is used (clear when adult chamber type is used)
