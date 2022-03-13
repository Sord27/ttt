Returns a string of 13 fields with the current status of the firmware update process.

Each field is separated by a space. Unless otherwise specified, each field is in decimal format.


| Field | Description | 
| ---- | ---- |
| 1 | Zero if update is in progress, non-zero if not |
| 2 | Bytes remaining to be uploaded |
| 3 | Total bytes to be uploaded |
| 4 | Total files to be uploaded |
| 5 | Files successfully uploaded |
| 6 | Total Bytes uploaded |
| 7 | Bytes uploaded for the current file |
| 8 | Bytes remaining for teh current file |
| 9 | File currently being uploaded |
| 10 | File upload attempts |
| 11 | Recorded file upload failures |
| 12 | Upload passes made |
| 13 | Pump reboots requested during upload |


The upload process will make up to 5 upload passes (tracked in field 12). In each pass every file available will be
 compared to the version of that file already loaded (if any). If a file requires uploading, up to 3 attempts will be
 made per pass to get a successful upload. If a file fails to upload 3 times it will be abandoned for that pass and the
 next file will be attempted. If there is a failure to successfully upload a file in a given pass, the pump will be
 rebooted in an attempt to automatically clear any error that might interfere with file uploading. The pump will also be
 rebooted after the successful upload of either the BLE or Smart-Pump files.