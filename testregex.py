# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 11:23:23 2020

@author: Oleksiy
"""

import re 
import sys
my_test_string = "listdata errorbar_yes 1.e-5 0.05263742 0.00026374 0.1293874892 "

pat1 = r"^listdata"
pat2 = r"errorbar_yes"
pat3 = r"listdata\s+errorbar_yes\s+(\d+\.?\d*e-?\d+\s|\d+\.\d+\s)(.+)"
pat4 = r"(\d+\.\d+ )"
res = re.search(pat3, my_test_string)

datastring = res.group(2)
print(datastring)

datapattern = r"(\d+\.\d+)"
newres = re.findall(datapattern, datastring)
newres = [float(q) for q in newres]
print(newres)


if res:
    print(res.group(0))
    print(res.group(1))
    print(res.group(2))
    print(res.lastindex)
    print(type(res.group(2)))
else:
    print("Result is None")
    
teststring = "config; blah nlahblah test1"
pat1 = r"^config\s*;([^;]*)"
res = re.search(pat1, teststring)
stringafter = re.findall(pat1,teststring)
print(stringafter)
print(len(stringafter))


teststring2 = "hello, hello2; hello3;"
print(teststring2.split(";"))

command_Cleardata_pattern = r"(clear_data|cleardata)\s+(all|\d{1,}\s*)"
teststring3 = "clear_data 13 "
print(re.search(command_Cleardata_pattern, teststring3)[0])
print(re.search(command_Cleardata_pattern, teststring3)[2])

aaa = "ajhsdakj"
if aaa:
    print("Blah")
else:
    print("No")
    
teststring4 = "         "

testlist = []
for q in testlist:
    print(q)