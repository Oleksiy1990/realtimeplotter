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

def Gaussian(x,center,sigma,amplitude):
    res = amplitude*np.exp(-0.5*np.power(x-center,2.)/np.power(sigma,2.))
    return res

while True:
    tau_decayingexp = 30
    val = ranf()*50
    val_random_error = ranf()*0.5
    val_random_errorbar = ranf()*0.5
    if np.abs(val_random_errorbar) < 1e-5:
        val_random_errorbar = 1e-5
    
    #my_information = "listdata errorbar_no {:.03f} {:.03f} {:.03f}".format(q,q/5,q/10)
    #my_information = "listdata errorbar_yes {:.03f} {:.03f} {:.03f}".format(val,np.sin(val),val/10)
    
    # the following function produces two sine waves with error bars
    #my_information = "listdata errorbar_yes {:.03f} {:.03f} {:.03f} {:.03f} {:.03f}".format(val,np.sin(val)+val_random_error,val_random_errorbar,np.sin(val/2)+val_random_error,val_random_errorbar)
    
    # the following produces damped sine
    #v0 = val
    #v1 = np.sin(v0)*np.exp(-v0/tau_decayingexp)+val_random_error
    #e1 = val_random_errorbar
    #v2 = np.sin(v0*0.75)*np.exp(-v0/tau_decayingexp)+val_random_error
    #e2 = val_random_errorbar
    #my_information = "listdata errorbar_yes {:.03f} {:.03f} {:.03f} {:.03f} {:.03f}".format(v0,v1,e1,v2,e2)
    
    
    
    center = 10
    sigma = 2
    amplitude = 3
    v0 = val
    v1 = Gaussian(v0,center,sigma,amplitude)+val_random_error
    e1 = val_random_errorbar
    v2 = Gaussian(v0,center+2,sigma,amplitude)+val_random_error+val_random_error
    e2 = val_random_errorbar
    my_information = "listdata errorbar_yes {:.03f} {:.03f} {:.03f} {:.03f} {:.03f}".format(v0,v1,e1,v2,e2)
    
    
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
    
    if q > 150:
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
doCropCurve = True
dofit = True

if doSetPlotTitle:
    message_str = message_str + "set_plot_title My test plot;"
if doSetAxisLabels:
    message_str = message_str + r"set_axis_labels my time [s], my yaxis [val];"
if doSetFitFunction:
    message_str = message_str + "set_fit_function gaussian;"     
if doSetCurveNumber:
    message_str = message_str + "set_curve_number 1;"
if doSetFitParameters:
    message_str = message_str + "setstartparams height : 2.5, center: 9.5, sigma: 2.5, verticaloffset: 0;"
if doCropCurve:
    message_str = message_str + "setCropTuple 20,40;"
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
