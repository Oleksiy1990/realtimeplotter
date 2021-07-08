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


if __name__ == "__main__":

    console_args = sys.argv
    MessageDicts = {}

    curvenum = int(console_args[1])
    command = console_args[2]

    mymethod_curvepeak = "doFit"
    myparams_curvepeak = {"fitFunction":"curvepeak",
                 "curveNumber": curvenum,
                 "startingParameters":{"numpeaks":1,
                                       "smoothing":0.1},
                    "fitMethod":"findmax",
                    "performFitting":""

                 }   
    mymessagedict_curvepeak = {"jsonrpc":"2.0", 
                 "method":mymethod_curvepeak,
                 "params":myparams_curvepeak,
                 "id":1}
    MessageDicts["curvepeak"] = mymessagedict_curvepeak


    r1 = json.dumps(MessageDicts[command])

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


