Returns a string with values for each LED, separated by spaces. E.g., `“1 1 1 1 1”`.

The LED states are reported in the following order:

`"<Server> <Internet> <Wi-Fi> <Pump> <Power>"`

Each value can be one of the following:

| Value | Description |
| ---- | ---- |
| 0 | Off |
| 1 | On |
| 4 | Flashing normally |
| 5 | Flashing fast |
| 6 | Flash slowly |

 