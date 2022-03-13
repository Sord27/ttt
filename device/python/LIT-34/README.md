To run script boson_reset_sp360_mlp.py, you need:

1 – Input CSV file with a list of MACs you want to run the script against. 2 – A Secret.json file containing the following:

'''json { " boson_url" : "Boson server url", " boson_username" : "Your Boson server login name ", " boson_password" : "Boson password for the devices", boson_ssh_key" : "Location to your SSH key",    "boson_port": "Boson SSH port number”} '''

To run the script:

'''python3 boson_reset_sp360_mlp.py input_file (Any file with extension csv will do) ''''
