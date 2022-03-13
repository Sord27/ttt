This command returns a string of hex characters that is composed of 8 32-bit hex numbers, e.g., 
`“000223460001E38600019924000317CE00000048000000240000002900000010”`.
There are no breaks between values.

`"<1><2><3><4><5><6><7><8>"`

| Position | Value |
| ---- | ---- |
| 1 | Seconds the pump has run in its lifetime |
| 2 | Seconds the pump deflation solenoid has been active |
| 3 | Seconds the right solenoid has been active |
| 4 | Seconds the left solenoid has been active |
| 5 | Pump activations |
| 6 | Deflation activations |
| 7 | Right solenoid activations |
| 8 | Left solenoid activations |