Sets whether the pump rails (forces data readings to min or max levels) analog-to-digital data by
passing a parameter:

| Value | Description | Behavior |
| --- | ------ | --------------------- |
| 0 | Disable | Normal operation |
| 1 | On activity | When pump is inflating or deflating, forces data to minimum or maximum |
| 2 | Interpolated | Forces interpolated data to maximum values so real data can be identified |
| 3 | Maximum | Forces all data to maximum values |
| 4 | Minimum | Forces all data to minimum values |