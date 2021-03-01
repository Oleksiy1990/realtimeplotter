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

def receive_message(socket_in):
    NUM_BYTES_PREAMBLE = 8
    
    preamble_bytes = socket_in.recv(NUM_BYTES_PREAMBLE)
    preamble_str = preamble_bytes.decode(encoding = "utf-8")
    
    message_length = int(preamble_str)
    if message_length == 0: # this signifies that communication is finished in this session
        return ""
    
    full_message_bytes = "".encode("utf-8")

    # this loop receives the message in chunks, of length at most self.buffersize
    while True:
        # if message length is less than buffersize, read it in one chunk and leave the loop
        if (message_length <= BUFFER_SIZE):
            data_bytes = socket_in.recv(message_length)
            full_message_bytes += data_bytes
            break
        # if message length is greater than buffersize, receive it in chunks
        else:
            data_bytes = socket_in.recv(BUFFER_SIZE)
            full_message_bytes += data_bytes
            message_length -= BUFFER_SIZE
    return full_message_bytes.decode("utf-8")



mymethod = "doClear"
myparams = {"clearData": "all"}
mymessagedict = {"jsonrpc":"2.0", 
                 "method":mymethod,
                 "params":myparams,
                 "id":1}
#print(mymessagedict)

mymethod3 = "addData"
myparams3 = {"dataPoint":{"curveNumber":5,"xval":0.2,
                            "yval":0.7,"yerr":0.05}}
mymessagedict3 = {"jsonrpc":"2.0", 
                 "method":mymethod3,
                 "params":myparams3,
                 "id":1}
#print(mymessagedict3)

mymethod2 = "setConfig"
myparams2 = {"axisLabels":["my_x","my_y"],"plotTitle":"my_plot_title",
             "plotLegend":{"curve1":"myfavcurve1"}}
mymessagedict2 = {"jsonrpc":"2.0", 
                 "method":mymethod2,
                 "params":myparams2,
                 "id":1}
#print(mymessagedict2)

datapts = [{"curveNumber":1,"xval":x,
                            "yval":np.sin(3*x),"yerr":0.05} for x in np.linspace(0,20,100)]

mymethod4 = "addData"
myparams4 = {"pointList":datapts}
mymessagedict4 = {"jsonrpc":"2.0", 
                 "method":mymethod4,
                 "params":myparams4,
                 "id":1}

mymethod5 = "doFit"
myparams5 = {"fitFunction":"sinewave",
             "curveNumber": 1,
             "startingParameters":{"frequency":3/(2*np.pi),
                                   "amplitude":1,
                                   "phase":0,
                                   "verticaloffset":0.},
             "fitMethod":"differential_evolution",
             #"fitterOptions":{"method":"trust-constr"},
             "performFitting":""}
mymessagedict5 = {"jsonrpc":"2.0", 
                 "method":mymethod5,
                 "params":myparams5,
                 "id":1}

mymessagedict6 = {"jsonrpc":"2.0", 
                 "method":"getFitResult",
                 "params":{"curveNumber":1},
                 "id":1}


r1 = json.dumps(mymessagedict6)
message_encoded = r1.encode("utf-8",errors="ignore")
message_length = len(message_encoded)

preamble = "{:08d}".format(message_length)
preamble_encoded = preamble.encode("utf-8",errors="ignore")
full_message = preamble_encoded + message_encoded

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

sendres = s.sendall(full_message)
if json.loads(r1)["method"] == "getFitResult":
    result_back = receive_message(s)
    print(result_back)

endmessage_str = "{:08d}".format(0)
endmessage_bytes = endmessage_str.encode("utf-8",errors="ignore")
s.sendall(endmessage_bytes)


s.close()


