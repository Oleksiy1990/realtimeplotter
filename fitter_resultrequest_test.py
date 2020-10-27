# -*- coding: utf-8 -*-
"""
Created on Sat Oct 24 22:58:03 2020

@author: Oleksiy
"""

import socket
import time
import sys
from numpy.random import ranf
import numpy as np

HOST = "127.0.0.1"
PORT = 5758
BUFFER_SIZE = 2048

msg_str = "getfitparams; 1"
msg_enc = msg_str.encode("utf-8")
preamble = "{:08d}".format(len(msg_enc))
preamble_enc = preamble.encode("utf-8")
full_message_enc = preamble_enc + msg_enc

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

sendres = s.sendall(full_message_enc)

full_msg_back_bytes = "".encode("utf-8")

msg_back_len = s.recv(8).decode(encoding="utf-8")
msg_back_len_int = int(msg_back_len)

data_bytes = s.recv(msg_back_len_int)
full_msg_back_bytes += data_bytes

result = full_msg_back_bytes.decode(encoding = "utf-8")

        

print(result)

endmessage_str = "{:08d}".format(0)
endmessage_bytes = endmessage_str.encode("utf-8",errors="ignore")
s.sendall(endmessage_bytes)

msg_back_len = s.recv(8).decode(encoding="utf-8")
msg_back_len_int = int(msg_back_len)

data_bytes = s.recv(msg_back_len_int)
full_msg_back_bytes += data_bytes

result = full_msg_back_bytes.decode(encoding = "utf-8")


s.close()
