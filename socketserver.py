# -*- coding: utf-8 -*-
"""
Created on Fri Aug 21 12:31:46 2020

@author: Oleksiy
"""
import socket 
from threading import Thread
import re


class TCPIPserver():
    def __init__(self,HOST,PORT,buffersize=2048,numconnections=5):
        self.buffersize = buffersize
        self.numconnections = numconnections
        self.serversocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.serversocket.bind((HOST,PORT))
        self.data_output = ""
        self.emit_data_immediately = True
        self.reportedLengthMessage = True

        self.received_msg_str = ""


    def clientsocket_parser(self,socket_in,newdata_signal,encoding = "utf-8"):
        """
        This function gets the incoming socket, receives the bytes, and 
        returns the string representation of the incoming message
        """
        if self.reportedLengthMessage is True:
            NUM_BYTES_PREFACE = 8
            while True:
                preface_bytes = socket_in.recv(NUM_BYTES_PREFACE)
                preface_str = preface_bytes.decode(encoding = encoding)
                #TODELETE
                print("clientsocket_parser: preface_str: ",preface_str)
                try:    
                    message_length = int(preface_str)
                    #TODELETE
                    print("clientsocket_parser: message_length = ",message_length)
                    if message_length == 0: # this signifies that communication is finished in this session
                        #TODELETE
                        print("clientsocket_parser: message_length = 0, closing the socket")
                        socket_in.close()
                        newdata_signal.emit("Done")
                        return None
                except:
                    print("Message from Class {:s} function clientsocket_parser: number of bytes of message cannot be converted to integer. Not reading any messages and not doing anything.".format(self.__class__.__name__))
                    socket_in.close()
                    newdata_signal.emit("")
                    return None # we just return an empty string in this case
                
                full_message_bytes = "".encode("utf-8")

                # this loop receives the message in chunks, of length at most self.buffersize
                while True:
                    if (message_length <= self.buffersize):
                        data_bytes = socket_in.recv(message_length)
                        full_message_bytes += data_bytes
                        break
                    else:
                        data_bytes = socket_in.recv(self.buffersize)
                        full_message_bytes += data_bytes
                        message_length -= self.buffersize # we subtract the number of already received bytes

                result = full_message_bytes.decode(encoding = encoding)
                self.data_output = result
                newdata_signal.emit(result)

        # now we tell what to do if the message length is not reported in advance
        #the only option in this case is that the other side closes the connection when the message is finished
        else:
            # first create an empty string, to which we will be adding data to save the full message
            full_message_bytes = "".encode("utf-8")
            while True:
                data_bytes = socket_in.recv(self.buffersize)
                if not data_bytes: # we stop receiving the message when the other side closed the connection
                    break
                full_message_bytes += data_bytes
            socket_in.close()
            result = full_message_bytes.decode(encoding = encoding)
            self.data_output = result
            return result

    # TODELETE This is NOT used
    def message_parser(self):
        if len(self.data_output) == 0:
            print("Message from Class {:s} function message_parser: apparently no message received, length of message string is 0. Not doing anything".format(self.__class__.__name__))
            return None

        listdata_pattern_errorbars_yes = r"listdata\s+errorbar_yes\s+(\d+\.?\d*e-?\d+\s|\d+\.\d+\s)(.+)"
        listdata_pattern_errorbars_no = r"listdata\s+errorbar_no\s+(\d+\.?\d*e-?\d+\s|\d+\.\d+\s)(.+)"
        search_errorbars_yes = re.search(listdata_pattern_errorbars_yes,self.data_output)
        if search_errorbars_yes:
            numerical_data_string = search_errorbars_yes.group(2)
            numerical_data = [float(val) for val in numerical_data_string]
            if len(numerical_data)%2 != 0: 
                print("Message from Class {:s} function message_parser: You provided not an even number of values. This is impossible, each measurement must come with an error bar, total number of transmitted values must be even. Not doing anything".format(self.__class__.__name__))
                return None
            measured_values = [numerical_data(q) for q in range(len(numerical_data)) if q%2 == 0]
            measured_errorbars = [numerical_data(q) for q in range(len(numerical_data)) if q%2 == 1]
            return True
        search_errorbars_no = re.search(listdata_pattern_errorbars_no,self.data_output)
        if search_errorbars_no:
            numerical_data_string = search_errorbars_yes.group(2)
            numerical_data = [float(val) for val in numerical_data_string]
            return True
        

    def listener_function(self):
        self.serversocket.listen(self.numconnections)
        while True:
            # accept connections from outside
            print("TCPIP server waiting for connections")
            (clientsocket, address) = self.serversocket.accept()
            
            # now do something with the clientsocket
            #print(type(address))
            print("Received connection from port {}".format(address))
            comm_processing_thread = Thread(target = self.clientsocket_parser,args = (clientsocket,),daemon=True)
            comm_processing_thread.start()
    
    def listener_function_Qt(self,newdata_signal):
        self.serversocket.listen(self.numconnections)
        while True:
            # accept connections from outside
            print("TCPIP server waiting for connections")
            (clientsocket, address) = self.serversocket.accept()
            
            # now do something with the clientsocket
            print("Received connection from port {}".format(address))
            received_msg_string = self.clientsocket_parser(clientsocket,newdata_signal)
            #newdata_signal.emit(received_msg_string)

    def __del__(self):
        self.serversocket.close()

def run_TCPIPserver(TCPIPserverclass,host,port,buffersize = 2048,numconnections=5):
    myServer = TCPIPserver(host,port,buffersize=buffersize,numconnections=numconnections)
    return None


if __name__ == "__main__":
    HOST = "127.0.0.1"
    PORT = 5757
    BUFFER_SIZE = 2048

    myServer = TCPIPserver(HOST,PORT)
    myServer.listener_function()
    
