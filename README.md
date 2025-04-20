
# HTTPS SERVER
<img src='https://github.com/HIPERION2021/HTTPS_PROJECT/blob/main/original-65207b4045b180f7c851927c630925d5.webp' />

HTTPS SERVER is an HTTPS implementation that includes ECDH key exchange, AES-GCM encryption, digital signatures and authentication via auth token.
This implementation is based on FLASK and is not designed for production.

## Necesary dependencies
Before using HTTPS SERVER please make sure you installed:
mysql-connector-python

HTTPS SERVER requires a MySQL database containing the provided tables.
If you are not used to SQL databases, please install lampp
run sudo /opt/lampp start
open the web browser and navigate to localhost (127.0.0.1)
select MyPHPAdmin
create a new database called "project_CSS"
select import
select the project_CSS.sql file provided in the server folder.

the lampp SQL server MUST be ACTIVE to use HTTPS SERVER.

To deactivate the SQL server please go to your terminal and write
sudo /opt/lampp/lampp stop


## Notes

Please note that this repo contains SSL certificates that wont work for your netwok. they are in place so you know where to put your own certificates
Please create new SSL certificates, if you are not familiar with the process you can run:
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
and put the ip address of your server computer in the CM (common name) value.
This is deprated and can be used only for testing. If you want to make thing right use a SAN file and add the ip as an alias.

## HOW TO USE HTTP SERVER

We devided the files you will need in two differnt folders
Server contains the files for your server machine.
Client contains the files you need to place in the client machine.

Please note, for convinience we added a client_id file and a token file so the transmissions can be made form the start using them.
The database also contains an active entry for the provided token.
If you want to test things you can just use them. 

If you delete the files you can expect the following:
The first time you send a message a different client_id file will be created in your client machine, and your client will notify you that you need a token
The server machine will automatically create a token specifically attached to the recently created client_id file.
The server database will activate that client_id / token combination for a period of one year.
You will need to move the token file to the client machine and place it in the same folder as your client script (There is no need for the file to stay in the server).

Cryptographic keys.
We added a digital signature to provide non-repudation and an extra layer of integrity (because redundancy is allways welcomed!!)
You can use the keys we provided. If you lose them or need to replace them you can run 

```bash
python3 tools.py
```
In any one of the machines and a new pair of keys will be generated. Please place the proved key in the client and the public key in the server.
If theres any error in the transmission your client machine will let you know. 
Messages that fail to be saved (for any reason) will be decrypted and saved as .bin files in the folder "received_messages"
If you dont see teh folder dont worry, our program will create it for you when needed.
You can see the contents of this messages using cat.
If everything goes well you will see the received mesage in your "data" table inside the MySQL database in the server.


## WHAT YOU SHOULD KNOW

This is not a production implementation, and as such, some details are not fully implemented. We use salt values for the authentication scheme BUT the objective is to explore how they work.
The salt implementation is NOT SECURE and should be modified if you want to use this program for any real-life purpose

The server side has databse configuration values hardcoded. This is NOT SECURE in real life. If you decide to use this code please create configuration files and isolate teh connection configurations from the rest of the code.

Our server expects certain fields to be transmited, if they are not present the message will be dump and saved in the received_messages folder.
You DO NOT need to change anything in the code. If you want to add or remove the values the server expects to get you can simply add or remove columns in the "data" table.
Please DO NOT change users table unless you fully understand how it works. This table is used for authentication and if you change it your client will fail to authenticate with the server.
Our program will make the necessary changes and updates as needed when the time comes.

## HOW TO SEND A MESSAGE

python3 https_client.py --server [server address:port] [json data]

[server address:port] = https://<server local ip address>:5000
[json data] = '{"FirstName":"somedata", "LastName":"some data", "Age":int, "Hight":float, "Address":"some data", "Comment":"some data"}'

Use example:

```bash
python3 https_client.py --server https://192.168.14.1:5000 '{"FirstName":"Pedro", "LastName":"Pascal", "Age":56, "Hight":1.78, "Address":"1578 Rainbow St. Apt 105", "Comments":"We are just testing this sever"}'
```

## CONTACT US

This is a research open source project, feel free to use it and modify it as needed. If you find any problem executing HTTPS SERVER please contact us. We will do our best to answer your questions.

## License

    Copyright [2025] [---------]

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
