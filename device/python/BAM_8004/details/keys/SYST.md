Returns 4 bytes that represent the status of the Sleep Expert to server connectivity.

# Byte 0: Wi-Fi #
| Value | Description|
| ---- | ---- |
| 0 | No valid status |
| 1 | Wi-Fi associated |
| 2 | Wi-Fi associated, but weak signal |
| 3 | Wi-Fi looking for SSID | 
| 4 | Wi-Fi bad password |
| 5 | Wi-Fi weak signal |
| 6 | Ethernet connected |

# Byte 1: Internet #
| Value | Description|
| ---- | ---- |
| 0 | No valid status |
| 1 | Internet connected |
| 2 | Internet connecting |
| 3 | Internet disconnected | 


# Byte 2: Server #
| Value | Description|
| ---- | ---- |
| 0 | No valid status |
| 1 | Connected to server |
| 2 | Server connecting |
| 3 | Connection error | 
| 4 | Server disconnected |
| 5 | Downloading RFS |
| 6 | Downloading Bammit |
| 7 | Can't get configuration file |
| 8 | Software download failed |

# Byte 3: Unused #