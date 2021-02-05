# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 18:24:43 2020

@author: Oleksiy
"""

import socket
import json
import sys
import numpy as np

HOST = "127.0.0.1"
PORT = 5757
BUFFER_SIZE = 2048


mymethod = "doClear"
myparams = {"clearData": "all"}
mymessagedict = {"jsonrpc":"2.0", 
                 "method":mymethod,
                 "params":myparams,
                 "id":1}
print(mymessagedict)

mymethod3 = "addData"
myparams3 = {"dataPoint":{"curveNumber":5,"xval":0.2,
                            "yval":0.7,"yerr":0.05}}
mymessagedict3 = {"jsonrpc":"2.0", 
                 "method":mymethod3,
                 "params":myparams3,
                 "id":1}
print(mymessagedict3)

mymethod2 = "setConfig"
myparams2 = {"axisLabels":["my_x","my_y"],"plotTitle":"my_plot_title"}
mymessagedict2 = {"jsonrpc":"2.0", 
                 "method":mymethod2,
                 "params":myparams2,
                 "id":1}
print(mymessagedict2)

datapts = [{"curveNumber":5,"xval":x,
                            "yval":np.sin(x),"yerr":0.05} for x in np.linspace(0,20,100)]

mymethod4 = "addData"
myparams4 = {"pointList":datapts}
mymessagedict4 = {"jsonrpc":"2.0", 
                 "method":mymethod4,
                 "params":myparams4,
                 "id":1}


r1 = json.dumps(mymessagedict4)
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



