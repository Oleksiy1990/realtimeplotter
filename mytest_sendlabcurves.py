# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 18:24:43 2020

@author: Oleksiy


This is for now for testing the fitter via the JSON remote interface

"""

import socket
import json
import sys
import numpy as np
import random

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

def generate_experimental_datalist(path,column):
    dataset = np.loadtxt(path + "/probCorrByIon.dat",skiprows=5)
    independentvar = dataset[:,0]
    dependentvar = dataset[:,column]
    errorvar = dataset[:,column+1]
    result = list(zip(independentvar,dependentvar,errorvar))
    return result
    

def generate_addData_message(datadict_list: list):
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    
    for msg in datadict_list:
        r1 = json.dumps(msg)

        message_encoded = r1.encode("utf-8",errors="ignore")
        message_length = len(message_encoded)

        preamble = "{:08d}".format(message_length)
        preamble_encoded = preamble.encode("utf-8",errors="ignore")
        full_message = preamble_encoded + message_encoded

        sendres = s.sendall(full_message)

    endmessage_str = "{:08d}".format(0)
    endmessage_bytes = endmessage_str.encode("utf-8",errors="ignore")
    s.sendall(endmessage_bytes)
    s.close()

if __name__ == "__main__":
    commandlineargs = sys.argv
    path = commandlineargs[1]
    
    datapts_list = []
    dictionary_list = []
    for (idx,val) in enumerate(commandlineargs[2:]):
        exp_points = generate_experimental_datalist(path,int(val))
        datapts = [{"curveNumber":idx,"xval":x[0],
                            "yval":x[1],"yerr":x[2]} for x in exp_points]
        #datapts_list.append(datapts)
        mymethod = "addData"
        myparams = {"pointList":datapts}
        mymessagedict = {"jsonrpc":"2.0", 
                         "method":mymethod,
                         "params":myparams,
                         "id":1}
        dictionary_list.append(mymessagedict)
    
    generate_addData_message(dictionary_list) 
