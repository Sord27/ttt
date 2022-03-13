Returns a list of devices in the pump proxy list. This is returned as a string of hex digits, 
e.g., `“03710151”`.

The first 2-digit byte indicates the number of devices that follow. 
Each subsequent 2-digit byte indicates a proxy device available.

| Value | Definition |
| ---- | ---- |
| `0x01` | Pump |
| `0x31` | Sense and Do |
| `0x41` | Foundation |
| `0x51` | Sleep Expert |
| `0x61` | Temperature Engine (V1) |
| `0x63` | Temperature Engine (V1.5) |
| `0x71` | MCR Proxy |
| `0x81` | Bridge Router |
| `0x91` | Smart Outlet |