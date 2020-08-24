import socket

HOST = "127.0.0.1"
PORT = 5757
BUFFER_SIZE = 8


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
my_information = "Here is my new interesting message\n"
my_information2 = "What's up here?"
message = my_information.encode("utf-8",errors="ignore")
sendres = s.sendall(message)
message = my_information2.encode("utf-8",errors="ignore")
sendres = s.sendall(message)
print("Sending message output : ",sendres)
s.close()
