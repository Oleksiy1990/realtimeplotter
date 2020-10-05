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

blah="10"
rawstrformat = r"({:s})\s+(all|\d{{1,}}\s*)".format(blah)
print(rawstrformat)


def process_setPlotLegend(input_pattern_raw_string,message_parts_list):
    full_SetPlotLegend_pattern = r"({:s})\s+(.*)".format(input_pattern_raw_string)
    print(full_SetPlotLegend_pattern)
    for individual_message in message_parts_list:
        search_res = re.search(full_SetPlotLegend_pattern,individual_message)
        if search_res:
            legend_labels_list = []
            legendLabels = search_res.group(2)
            allLegendLabels = legendLabels.split(",")
            for legendlabel in allLegendLabels:
                individual_label_pattern = r"(curve|Curve)(\d{1,2})\s+(.*)"
                individual_label_search_res = re.search(individual_label_pattern,legendlabel)
                if individual_label_search_res:
                    curve_num = int(individual_label_search_res.group(2))
                    legend_string = individual_label_search_res.group(3)
                    legend_labels_list.append((curve_num,legend_string))
            message_parts_list.remove(individual_message)
            return ("set_plot_legend",legend_labels_list)
    return None

input_pattern_raw_string = r"setPlotLegend"
message_parts_list = ["setPlotLegend Curve0 blah 00, Curve2 blah 02 ", "blah blah blahlahlah"]

res = process_setPlotLegend(input_pattern_raw_string,message_parts_list)
print(res)

datastring = res.group(1)
print("Datastring: ",datastring)

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
    