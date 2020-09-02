import socket
import time
import sys
from numpy.random import ranf
import numpy as np

HOST = "127.0.0.1"
PORT = 5757
BUFFER_SIZE = 2048

q = 0




s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
#my_information = "listdata errorbar_no {:.03f} {:.03f} {:.03f}".format(q,q/5,q/10)
my_information = "config; clear_data all"
message = my_information.encode("utf-8",errors="ignore")
sendres = s.sendall(message)
#message = my_information2.encode("utf-8",errors="ignore")
#sendres = s.sendall(message)
s.close()

while True:
    val = ranf()*30
    val_random_error = ranf()*0.5
    val_random_errorbar = ranf()*0.5
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    #my_information = "listdata errorbar_no {:.03f} {:.03f} {:.03f}".format(q,q/5,q/10)
    #my_information = "listdata errorbar_yes {:.03f} {:.03f} {:.03f}".format(val,np.sin(val),val/10)
    my_information = "listdata errorbar_yes {:.03f} {:.03f} {:.03f}".format(val,np.sin(val)+val_random_error,val_random_errorbar)
    #my_information = "listdata errorbar_no {:.03f} {:.03f} {:.03f} {:.03f}".format(val,np.sin(val),val/10,np.log(val))
    
    #my_information2 = "What's up here?"
    message = my_information.encode("utf-8",errors="ignore")
    sendres = s.sendall(message)
    #message = my_information2.encode("utf-8",errors="ignore")
    #sendres = s.sendall(message)
    #print("Sending message output : ",sendres)
    s.close()
    q += 1
    time.sleep(0.01)
    
    if q > 50:
        break

sys.exit(0)
time.sleep(3)
print("Trying to clear data")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
#my_information = "listdata errorbar_no {:.03f} {:.03f} {:.03f}".format(q,q/5,q/10)
my_information = "config; clear_data all"
message = my_information.encode("utf-8",errors="ignore")
sendres = s.sendall(message)
#message = my_information2.encode("utf-8",errors="ignore")
#sendres = s.sendall(message)
s.close()

sys.exit(0)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
#my_information = "listdata errorbar_no {:.03f} {:.03f} {:.03f}".format(q,q/5,q/10)
my_information = "config; set_axis_labels newx, newy ; setplottitle MyFavoriteTitle"
message = my_information.encode("utf-8",errors="ignore")
sendres = s.sendall(message)
#message = my_information2.encode("utf-8",errors="ignore")
#sendres = s.sendall(message)
s.close()

sys.exit(0)


time.sleep(5)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
#my_information = "listdata errorbar_no {:.03f} {:.03f} {:.03f}".format(q,q/5,q/10)
my_information = "clear_plot"
message = my_information.encode("utf-8",errors="ignore")
sendres = s.sendall(message)
#message = my_information2.encode("utf-8",errors="ignore")
#sendres = s.sendall(message)
#print("Sending message output : ",sendres)
s.close()
 
