# -*- coding: utf-8 -*-
"""
Created on Fri Aug 21 12:31:46 2020

@author: Oleksiy
"""
import socket 
from threading import Thread, Lock
from interpreter import message_interpreter_twoway
from functools import partial
from helperfunctions import create_JSONRPC_errormessage, send_TCPIP_message


class TCPIPserver():
    def __init__(self,HOST,PORT,buffersize=2048,numconnections=5):
        self.buffersize = buffersize
        self.numconnections = numconnections
        self.serversocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.serversocket.bind((HOST,PORT))
        self.data_output = ""
        self.reportedLengthMessage = True

        self.received_msg_str = ""

        #self.lock_for_transmission = Lock() # this is basically in order to get results
        # from the fitter without something else happening in the meantime

    def clientsocket_parser(self,socket_in,workersignals,encoding = "utf-8") -> bool:
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
        # =========== Here we read the message from the client
        # The case when the message comes with a preamble
        if self.reportedLengthMessage is True:
            NUM_BYTES_PREAMBLE = 8 # Preamble is a string of exactly 8 characters, just at the beginning of the main message
            # those characters are converted into an integer, which determines how many bytes will be read
            # Remember that in this case the socket is basically hanging in the while True loop until 00000000 is received
            while True:

                try:
                    preamble_bytes = socket_in.recv(NUM_BYTES_PREAMBLE)
                    preamble_str = preamble_bytes.decode(encoding=encoding)
                    # If the communication has finished or we got an illegal preamble, we send error message back
                    # If the preamble is not convertible to an integer: "Illegal preamble"
                    message_length = int(preamble_str)
                    if message_length == 0: # this signifies that communication is finished in this session
                        socket_in.close()
                        workersignals.set_client_communication_socket.emit(None) # This is done to reset the client communication socket
                        return True
                except:
                    print(
                        """Message from Class {:s} function clientsocket_parser: 
                        number of bytes of message cannot be converted to integer. 
                        Not reading any messages and not doing anything.""".format(self.__class__.__name__))
                    json_message_string = create_JSONRPC_errormessage(-32000, "Illegal preamble")
                    send_TCPIP_message(socket_in, json_message_string, True)
                    socket_in.close()
                    workersignals.set_client_communication_socket.emit(None)
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
                workersignals.set_client_communication_socket.emit(socket_in)
                workersignals.newdata.emit(result)

        # TODO: Implement the case for messages without reported length
        # ======= The one without reported length messages is not yet implemented well
        # this is now the case when the message length is not reported in advance.
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
            workersignals.newdata.emit(result)
            return True


    def listener_function_Qt(self,workersignals):
        self.serversocket.listen(self.numconnections)
        while True:
            # accept connections from outside
            print("TCPIP server waiting for connections")
            (clientsocket, address) = self.serversocket.accept()
            
            # now do something with the clientsocket
            print("Received connection from port {}".format(address))
            isClientSocketParserSuccess = self.clientsocket_parser(clientsocket,workersignals)
            if isClientSocketParserSuccess is False:
                print(
                    """
                    Message from Class {:s} function listener_function_Qt: 
                    clientsocket_parser returned False. 
                    Check the messages that you are sending to it via TCP/IP.
                    """.format(self.__class__.__name__)
                )

    # TODELETE I don't think this destructor should be used
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
    
