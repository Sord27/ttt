To test the script, you need:

1 – Input CSV file with a list of MACs you want to run the script against.
2 – A Secret.json file containing the following:

'''json
{
"backendServer_UserName" : "Your MEDUI login",
"backendServer_Password" : "Your MEDUI password",
"boson_User" : "Your MEDUI-Boson log",
"boson_Password" : "YouMEDUI-Boson Password",
"server" : "Production ADMIN URL ",
"bosonServer" : "Production Admin URL for Boson access" 
}
'''

To run the script:

'''bash 
python rpc_3.py input.csv (Any file with extension csv will do)
''''