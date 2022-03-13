The Wi-Fi status key will return the current Wi-Fi status of the device.

The output of the Wi-Fi Scan request is a JSON formatted string that will contain the following keys, through some are optional based on the connection status:

| Item | Value |
| ---- | ---- |
| state | state of the wifi connection. See table below |
| ssid | name of the configured network |
| bssid | MAC address of the base station |
| signal | signal stength in dBm, if SSID found |
| quality | signal quality in %, if SSID fount |
**Note:** bssid, signal, and quality only show if the SSID is found

# State table #
| Value | Description |
| ---- | ---- |
| 0 | Using Ethernet |
| 1 | Looking for SSID |
| 2 | Associated with SSID | 
| 3 | Bad Password | 
| 4 | Associated |
| 5 | Disconnected |
| 6 | Unknown |

# Example return value #
~~~~
[
    “state”:4,
    "ssid":"shyster2",
    "bssid":"45:78:23:fe:45:11",
    "security":"WPA",
    "signal":-45,
    "quality":55
]
~~~~
**Note:** If using Ethernet (state = 0), the only other key returned is "bssid", which will represent the MAC address of the Ethernet adapter.
