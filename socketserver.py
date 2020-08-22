# -*- coding: utf-8 -*-
"""
Created on Fri Aug 21 12:31:46 2020

@author: Oleksiy
"""
import socket 
from threading import Thread

HOST = "127.0.0.1"
PORT = 5757
BUFFER_SIZE = 8

serversocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
serversocket.bind((HOST,PORT))
serversocket.listen(5)


def clientsocket_parser(socket_in,output_tuple,encoding = "utf-8"):
    full_message = "".encode("utf-8")
    while True:
        data = socket_in.recv(BUFFER_SIZE)
        if not data: 
            break
        full_message += data
    socket_in.close()
    output_tuple = (True,full_message.decode(encoding=encoding)) # so this is supposed to return a string
    print("Here is the output: ",output_tuple)


output_tuple = (False,"")

while True:
    # accept connections from outside
    print("socketserver waiting for connections")
    (clientsocket, address) = serversocket.accept()
    
    # now do something with the clientsocket
    print(type(address))
    print("Received connection from port {}".format(address))
    comm_processing_thread = Thread(target = clientsocket_parser,args = (clientsocket,output_tuple),daemon=True)
    comm_processing_thread.start()


