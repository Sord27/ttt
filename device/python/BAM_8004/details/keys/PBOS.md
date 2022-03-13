This returns a string of 5 contiguous, undifferentiated bytes representing the current status of all 5 possible Smart Outlets. Each byte is a bit mask, interpreted as follows:

| Value | 1 | 0 |
| --- | ------------------ | ----- |
| `0x01` | 120V socket is on | 120V socket is off |
| `0x02` | 12V light is on | 12V light is off |
| `0x04` | Smart Outlet has not cleared the status change flag. Command still pending | | 
| `0x10` | Smart Outlet is unused | |