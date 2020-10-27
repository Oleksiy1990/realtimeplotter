# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 20:22:18 2020

@author: Oleksiy
"""

import socket
import time
import json

# create TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)



server_address = ("localhost", 12345)
print ('starting up on %s port %s' % server_address)
sock.bind(server_address)

# listen for incoming connections (server mode) with one connection at a time
sock.listen(1)

while True:
    # wait for a connection
    time.sleep(1)
    print ('waiting for a connection')
    connection, client_address = sock.accept()
    running_data_bytes = "".encode("utf-8")
    try:
        # show who connected to us
        print ('connection from', client_address)

        # receive the data in small chunks and print it
        while True:
            data = connection.recv(64)
            if data:
                running_data_bytes += data
                # output received data
                print ("Data: %s" % data)
            else:
                # no more data -- quit the loop
                print ("no more data.")
                output_bytes = running_data_bytes
                result_str = output_bytes.decode("utf-8")
                result_dict = json.loads(result_str)
                print(result_dict)
                print(type(result_dict))
                print(result_dict["key1"])
                print(type(result_dict["key1"]))
                break
    finally:
        # Clean up the connection
        connection.close()