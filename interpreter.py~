# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 14:27:15 2020

@author: Oleksiy
"""

import re

def message_interpreter(message = ""):
   
    if len(message) == 0:
        print("Function message_interpreter: apparently no message received, length of message string is 0. Not doing anything")
        return [("nofunction",message)]

    listdata_pattern_errorbars_yes = r"listdata\s+errorbar_yes\s+(\d+\.?\d*e-?\d+\s|\d+\.\d+\s)(.+)"
    listdata_pattern_errorbars_no = r"listdata\s+errorbar_no\s+(\d+\.?\d*e-?\d+\s|\d+\.\d+\s)(.+)"
    search_errorbars_yes = re.search(listdata_pattern_errorbars_yes,message)
    if search_errorbars_yes:
        x_val = float(search_errorbars_yes.group(1))
        numerical_data_part = search_errorbars_yes.group(2)
        numerical_datapattern = r"(-?\d+\.\d+)"
        numerical_data_string_array = re.findall(numerical_datapattern,numerical_data_part)
        numerical_data = [float(val) for val in numerical_data_string_array]
        if len(numerical_data)%2 != 0: 
            print("Function message_interpreter: You provided not an even number of values. This is impossible, each measurement must come with an error bar, total number of transmitted values must be even. Not doing anything")
            return [("nofunction",message)]
        measured_values = [numerical_data[q] for q in range(len(numerical_data)) if q%2 == 0]
        measured_errorbars = [numerical_data[q] for q in range(len(numerical_data)) if q%2 == 1]
        return [("generate_plot_pointbypoint",(x_val,measured_values,measured_errorbars))]
    search_errorbars_no = re.search(listdata_pattern_errorbars_no,message)
    if search_errorbars_no:
        x_val = float(search_errorbars_no.group(1))
        numerical_data_part = search_errorbars_no.group(2)
        numerical_datapattern = r"(-?\d+\.\d+)"
        numerical_data_string_array = re.findall(numerical_datapattern,numerical_data_part)
        measured_values = [float(val) for val in numerical_data_string_array]
        return [("generate_plot_pointbypoint",(x_val,measured_values))]
    
    clearplot_pattern = r"^clear_plot"
    if re.search(clearplot_pattern,message):
        return [("clear_plot","")]

    config_command_pattern = r"^config\s*;(.*)"
    if re.search(config_command_pattern,message):
        config_command_list = config_interpreter(message)
        return config_command_list
    
    # This must be at the end, this is if everything else fails
    return [("nofunction",message)]

def config_interpreter(fullmessage = ""):
    """
    The idea is that the function message_interpreter calls config_interpreter as a helper function 
    """

    output_command_list = []
    if not isinstance(fullmessage,str):
        print("Message from function config_interpreter: The message is not a string. Not doing anything")
        output_command_list.append(("nofunction",""))
        return output_command_list

    message_parts_list = fullmessage.split(";") # Important point: the commands must be split with semicolons

    if len(message_parts_list) < 1: 
        print("Message from function config_interpreter: you must specify at least config; and one more command in your string. Not doing anything")
        output_command_list.append(("nofunction",fullmessage))
        return output_command_list

    #delete "config" from message_parts_list
    command_config_pattern = r"config\s*"
    for individual_message in message_parts_list:
        search_res = re.search(command_config_pattern,individual_message)
        if search_res:
           message_parts_list.remove(individual_message)
    
    command_Cleardata_pattern = r"(clear_data|cleardata)\s+(all|\d{1,}\s*)"
    for individual_message in message_parts_list:
        search_res = re.search(command_Cleardata_pattern,individual_message)
        if search_res:
           output_command_list.append(("clear_data",search_res.group(2)))
           message_parts_list.remove(individual_message)

    command_SetAxislabels_pattern = r"(set_axis_labels|setaxislabels|setAxisLabels)\s+(.*)"
    for individual_message in message_parts_list:
        search_res = re.search(command_SetAxislabels_pattern,individual_message)
        if search_res:
            axisLabels = search_res.group(2)
            each_axis_label = axisLabels.split(",")
            if len(each_axis_label) == 2:
                output_command_list.append(("set_axis_labels",each_axis_label))
            else:
                print("Message from function config_interpreter: set_axis_labels argument must be two strings separated by a comma. Command must be of the form: set_axis_labels myFavorite X , myFavorite Y; Now it's not in that form. Not labeling axes")
            message_parts_list.remove(individual_message)

    command_SetPlotTitle_pattern = r"(set_plot_title|setplottitle|setPlotTitle)\s+(.*)"
    for individual_message in message_parts_list:
        search_res = re.search(command_SetPlotTitle_pattern,individual_message)
        if search_res:
            plottitle = search_res.group(2)
            output_command_list.append(("set_plot_title",plottitle))
            message_parts_list.remove(individual_message)
    
    command_setPlotLegend_pattern = r"(set_plot_legend|setplotlegend|setPlotLegend)\s+(.*)"
    for individual_message in message_parts_list:
        search_res = re.search(command_setPlotLegend_pattern,individual_message)
        if search_res:
            legendLabels = search_res.group(2)
            allLegendLabels = legendLabels.split(",")
            output_command_list.append(("set_plot_legend",allLegendLabels))
            message_parts_list.remove(individual_message)
    
    for individual_message in message_parts_list:
        if individual_message.isspace() or (individual_message == ""):
            message_parts_list.remove(individual_message)
    if len(message_parts_list) > 0:
        print("Warning from function config_interpreter: you probably made mistakes in the syntax of some commands. There are commands that you sent and that could not be parsed: {}".format(message_parts_list))

    return output_command_list
