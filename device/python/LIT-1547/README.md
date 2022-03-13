# Extracting responsive air (RA) log #
This tool used to pull RA log from the device (pump) through Boson connection.
It uses python multiprocessing module, it acquires the log for each device, however the nature multiprocessing will not have the output in sequential order.

## Requirements ##
* Python 3.7 or later
* The requirements.txt file contains the prerequisite modules
* The secert.json should be configured with the following:
```json
{
    "boson_url": "URL to Boson server",
    "boson_username": "Your Boson user name",
    "boson_password": "Password to access the device",
    "boson_ssh_key" : "Path to you rsa file",
    "boson_port": "Boson port"
}
```
## How to Use ##
```bash
    python3 get_bio_rad.py <input_file_name>
```
### Note ###
The input file should contain a list of the MAC(s) need to be processed in one column.