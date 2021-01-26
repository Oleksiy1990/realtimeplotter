# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 18:24:43 2020

@author: Oleksiy
"""

import socket
import json
import sys

HOST = "127.0.0.1"
PORT = 5757
BUFFER_SIZE = 2048


mymethod = "config"
myparams = {"clearData": "all"}
mymessagedict = {"jsonrpc":"2.0", 
                 "method":mymethod,
                 "params":myparams,
                 "id":1}
print(mymessagedict)

r1 = json.dumps(mymessagedict)
message_encoded = r1.encode("utf-8",errors="ignore")
message_length = len(message_encoded)

preamble = "{:08d}".format(message_length)
preamble_encoded = preamble.encode("utf-8",errors="ignore")
full_message = preamble_encoded + message_encoded

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

sendres = s.sendall(full_message)
endmessage_str = "{:08d}".format(0)
endmessage_bytes = endmessage_str.encode("utf-8",errors="ignore")
s.sendall(endmessage_bytes)
s.close()



