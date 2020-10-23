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
        
        There are two acceptable approaches to receiving messages on a TCP/IP server:
        1) adding a preamble of known length to every message, which will tell how many bytes a message has
        2) closing the connection after having sent a message (on the client side). In this case, one 
            listens until the read() function returns zero bytes. 
        In this case, self.reportedLengthMessage detemines whether each message comes with a preamble 
        telling how many bytes the message will be, or whether the client is expected to close the connection 
        after sending a full message
        """

        # The case when the message comes with a preamble
        if self.reportedLengthMessage is True:
            NUM_BYTES_PREAMBLE = 8 # Preamble is a string of exactly 8 characters, just at the beginning of the main message
            # those characters are converted into an integer, which determines how many bytes will be read
            # Remember that in this case the socket is basically hanging in the while True loop until 00000000 is received
            while True:
                preamble_bytes = socket_in.recv(NUM_BYTES_PREAMBLE)
                preamble_str = preamble_bytes.decode(encoding = encoding)
                try:    
                    message_length = int(preamble_str)
                    if message_length == 0: # this signifies that communication is finished in this session
                        socket_in.close()
                        newdata_signal.emit("Done") # if the communication is finished, is sends "Done" to the main program
                        return True
                except:
                    print("Message from Class {:s} function clientsocket_parser: number of bytes of message cannot be converted to integer. Not reading any messages and not doing anything.".format(self.__class__.__name__))
                    socket_in.close()
                    newdata_signal.emit("")
                    return False
                
                full_message_bytes = "".encode("utf-8")

                # this loop receives the message in chunks, of length at most self.buffersize
                while True:
                    # if message length is less than buffersize, read it in one chunk and leave the loop
                    if (message_length <= self.buffersize):
                        data_bytes = socket_in.recv(message_length)
                        full_message_bytes += data_bytes
                        break
                    # if message length is greater than buffersize, receive it in chunks
                    else:
                        data_bytes = socket_in.recv(self.buffersize)
                        full_message_bytes += data_bytes
                        message_length -= self.buffersize # we subtract the number of already received bytes
                # Here the data is decoded into a string and sent to the main program via the emit() function, but
                #note that the code is still sitting in the outer while True loop waiting for 00000000 to exit the function 
                result = full_message_bytes.decode(encoding = encoding)
                newdata_signal.emit(result)

        # this is now the case when the message length is not reported in advance. 
        #the function exits when the other side (client) closes the communication, which means that the entire 
        #message has been sent 
        # This is generally the preferred and cleaner way
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
            newdata_signal.emit(result)
            return True

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
            isClientSocketParserSuccess = self.clientsocket_parser(clientsocket,newdata_signal)
            if isClientSocketParserSuccess is False:
                print("Message from Class {:s} function listener_function_Qt: clientsocket_parser returned False. Check the messages that you are sending to it via TCP/IP.".format(self.__class__.__name__))

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
    
