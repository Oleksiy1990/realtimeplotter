import socket
import time
import sys
from numpy.random import ranf
import numpy as np

HOST = "127.0.0.1"
PORT = 5757
BUFFER_SIZE = 2048

q = 0


doClearData = True
if doClearData:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    my_information = "config; clear_data all"
    message_encoded = my_information.encode("utf-8",errors="ignore")
    message_length = len(message_encoded)
    preamble = "{:08d}".format(message_length)
    preamble_encoded = preamble.encode("utf-8",errors="ignore")
    full_message = preamble_encoded + message_encoded
    
    sendres = s.sendall(full_message)
    
    endmessage_str = "{:08d}".format(0)
    print(endmessage_str)
    endmessage_bytes = endmessage_str.encode("utf-8",errors="ignore")
    s.sendall(endmessage_bytes)
    s.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

while True:
    val = ranf()*30
    val_random_error = ranf()*0.5
    val_random_errorbar = ranf()*0.5
    
    #my_information = "listdata errorbar_no {:.03f} {:.03f} {:.03f}".format(q,q/5,q/10)
    #my_information = "listdata errorbar_yes {:.03f} {:.03f} {:.03f}".format(val,np.sin(val),val/10)
    my_information = "listdata errorbar_yes {:.03f} {:.03f} {:.03f} {:.03f} {:.03f}".format(val,np.sin(val)+val_random_error,val_random_errorbar,np.sin(val/2)+val_random_error,val_random_errorbar)
    #my_information = "listdata errorbar_no {:.03f} {:.03f} {:.03f} {:.03f}".format(val,np.sin(val),val/10,np.log(val))
    
    #my_information2 = "What's up here?"
    message_encoded = my_information.encode("utf-8",errors="ignore")
    message_length = len(message_encoded) # 1 is for the space before the actual data
    print("Data message length: ",message_length)
    preamble = "{:08d}".format(message_length)
    preamble_encoded = preamble.encode("utf-8",errors="ignore")
    full_message = preamble_encoded + message_encoded
    
    sendres = s.sendall(full_message)
    
    #s.close()
    q += 1
    time.sleep(0.01)
    
    if q > 50:
        preamble = "{:08d}".format(0) # if we send "00000000", the socket on the other side will be closed
        preamble_encoded = preamble.encode("utf-8",errors="ignore")
        s.sendall(preamble_encoded)
        break

s.close()
#sys.exit()

message_str = "config;"
doSetPlotTitle = True
doSetAxisLabels = True
doSetFitFunction = True
doSetCurveNumber = True 
doSetFitParameters = True
doSetCurveNumber = True
dofit = True

if doSetPlotTitle:
    message_str = message_str + "set_plot_title My test plot;"
if doSetAxisLabels:
    message_str = message_str + "set_axis_labels my xaxis, my yaxis;"
if doSetFitFunction:
    message_str = message_str + "set_fit_function sinewave;"     
if doSetCurveNumber:
    message_str = message_str + "set_curve_number 1;"
if doSetFitParameters:
    message_str = message_str + "setstartparams frequency : 0.1, amplitude: 1.0, phase: 0, verticaloffset: 0;"
if dofit:
    message_str = message_str + "dofit ;"
    
print("Full message: ",message_str)
message_encoded = message_str.encode("utf-8",errors="ignore")
message_length = len(message_encoded)
preamble = "{:08d}".format(message_length)
preamble_encoded = preamble.encode("utf-8",errors="ignore")
full_message = preamble_encoded + message_encoded

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
sendres = s.sendall(full_message)

preamble = "{:08d}".format(0)
preamble_encoded = preamble.encode("utf-8",errors="ignore")
s.sendall(preamble_encoded)
s.close()

sys.exit(0)
