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
    
MessageDicts = {}

valuesrange = 50
numpoints = 100
xvals = np.random.rand(numpoints)*valuesrange # numpoints is the points between 0 and 1, valuesrange then extends the range 
datapts = [{"curveNumber":1,"xval":x,
                            "yval":np.sin(3*x) + random.random()-0.5,"yerr":0.05} for x in xr]

datapts_Gaussian = [{"curveNumber":1,"xval":x,
                            "yval":np.exp(-np.power(x-25.,2)/10) + (random.random()-0.5),"yerr":0.05} for x in xr]

datapts_parabolic = [{"curveNumber":1,"xval":x,
                            "yval":2*np.power(x-25,2.) +5*(x-25) - 20 + 50*(random.random()-0.5),"yerr":0.05} for x in xr]

datapts_linear = [{"curveNumber":1,"xval":x,
                            "yval":2*x - 20 + 50*(random.random()-0.5),"yerr":0.05} for x in xr]
mymethod4 = "addData"
myparams4 = {"pointList":datapts_linear}
mymessagedict4 = {"jsonrpc":"2.0", 
                 "method":mymethod4,
                 "params":myparams4,
                 "id":1}

MessageDicts["generatedData"] = mymessagedict4
