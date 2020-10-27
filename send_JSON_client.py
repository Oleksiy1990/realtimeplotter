# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 18:24:43 2020

@author: Oleksiy
"""

import socket
import json
import sys

HOST = "127.0.0.1"
PORT = 12345
BUFFER_SIZE = 64

mytestdict = {"key1":10,"key2":"blahblah","key3":{"subkey1":1,"subkey2":2}}
print(mytestdict)

r1 = json.dumps(mytestdict,indent=4)
msg = r1.encode("utf-8")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

sendres = s.sendall(msg)

s.close()

