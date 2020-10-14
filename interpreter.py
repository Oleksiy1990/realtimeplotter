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
    
    # define regular expression patterns for reading data that includes 
    #or does not include error bars. Make sure to send data as floats, scientific 
    #notation is accepted
    # Here the pattern searches for errorbar yes or no, and then the x-value, the data 
    #itself is pattern-matched later
    listdata_pattern_errorbars_yes = r"listdata\s+errorbar_yes\s+(\d+\.?\d*e-?\d+\s|\d+\.\d+\s)(.+)"
    listdata_pattern_errorbars_no = r"listdata\s+errorbar_no\s+(\d+\.?\d*e-?\d+\s|\d+\.\d+\s)(.+)"
    
    # first we check if the pattern errorbars_yes gives a result
    search_errorbars_yes = re.search(listdata_pattern_errorbars_yes,message)
    if search_errorbars_yes:
        x_val = float(search_errorbars_yes.group(1))
        numerical_data_part = search_errorbars_yes.group(2) # This is not analyzed in the first pattern
        # Now we will match the numerical data. Send it as a float, no scientific notation 
        numerical_datapattern = r"(-?\d+\.\d+)" 
        numerical_data_string_array = re.findall(numerical_datapattern,numerical_data_part)
        numerical_data = [float(val) for val in numerical_data_string_array]
        if len(numerical_data)%2 != 0: 
            print("Function message_interpreter: You provided not an even number of values. This is impossible, each measurement must come with an error bar, total number of transmitted values must be even. Not doing anything")
            return [("nofunction",message)]
        measured_values = [numerical_data[q] for q in range(len(numerical_data)) if q%2 == 0]
        measured_errorbars = [numerical_data[q] for q in range(len(numerical_data)) if q%2 == 1]
        return [("generate_plot_pointbypoint",(x_val,measured_values,measured_errorbars))]
    
    # Now we will try to match the pattern that assumes no error bars 
    #If there are error bars, this match will fail and the if-statement will not run
    search_errorbars_no = re.search(listdata_pattern_errorbars_no,message)
    if search_errorbars_no:
        x_val = float(search_errorbars_no.group(1))
        numerical_data_part = search_errorbars_no.group(2)
        numerical_datapattern = r"(-?\d+\.\d+)"
        numerical_data_string_array = re.findall(numerical_datapattern,numerical_data_part)
        measured_values = [float(val) for val in numerical_data_string_array]
        return [("generate_plot_pointbypoint",(x_val,measured_values))]
    
    # TODO: Not sure if this should stay here. Maybe get rid of this 
    clearplot_pattern = r"^clear_plot"
    if re.search(clearplot_pattern,message):
        return [("clear_plot","")]

    """
    The way this function is written now is that either we send data points in real time
    in which case we will generate plot point by point, and so every point gets
    pattern-matched and sent to the processor, or we send configurations 
    The configurations are suposed to deal with things like plot labels, 
    fitting initial values, etc etc
    """
    config_command_pattern = r"^config\s*;(.*)"
    config_search_result = re.search(config_command_pattern,message)
    if config_search_result:
        config_command_list = config_interpreter(config_search_result.group(1)) 
        # message.group(1) is what is matched in brackets, not the word "config" itself
        return config_command_list
    
    # This must be at the end, this is if all other pattern matching fails, meaning
    #no valid command was sent. We then sent "nofunction" to the main program
    #so that it tells the user that the pattern matching failed and commands are invalid
    return [("nofunction",message)]

def config_interpreter(fullmessage = ""):
    """
    fullmessage is the entire string that comes after config;
    The idea is that the function message_interpreter calls config_interpreter as a helper function 
    """
    
    # This dictionary holds all possible commands that can be sent
    #in the config string
    config_command_dictionary = {"process_cleardata" : r"clear_data|cleardata",
        "process_setAxisLabels" : r"set_axis_labels|setaxislabels|setAxisLabels",
        "process_setPlotTitle" : r"set_plot_title|setplottitle|setPlotTitle",
        "process_setPlotLegend" : r"set_plot_legend|setplotlegend|setPlotLegend",
        "process_setFitFunction" : r"setfitfunction|set_fit_function",
        "process_setCurveNumber" : r"setcurvenumber|set_curve_number",
        "process_setStartingParameters" : r"setstartparams|setstartparameters|set_starting_values|set_starting_params|set_starting_parameters",
        "process_doFit" : r"dofit|doFit|do_fit"}

    # This is the list of the commands that will be returned back to the message_interpreter, and
    #then to the main program
    output_command_list = []
    if not isinstance(fullmessage,str):
        print("Message from function config_interpreter: The message is not a string. Not doing anything")
        output_command_list.append(("nofunction",""))
        return output_command_list

    # We will split the message string into parts now, where the parts are separated 
    #using semicolons
    message_parts_list = fullmessage.split(";") 

    if len(message_parts_list) < 1: 
        print("Message from function config_interpreter: you must specify at least config; and one more command in your string. Not doing anything")
        output_command_list.append(("nofunction",fullmessage))
        return output_command_list

    # We will go through the config_command_dictionary and check the configuration string for the list of all
    #available commands
    for (function,input_pattern) in config_command_dictionary.items():
        try:
            function_to_call = globals()[function]
        except:
            print("Such a function is not defined. Check your config_command_dictionary and make sure that the function with the name {} is defined in file interpreter.py".format(function))
            continue
        # if we found the function in config_command_dictionary, we call it and feed the 
        #message_parts_list to it
        function_output = function_to_call(input_pattern,message_parts_list)
        # if the function fails, the output should be None, otherwise, it will be a command that can be 
        #sent to the main program, and we append that command to the output_command_list
        if function_output is not None:
            output_command_list.append(function_output)

    # Now we check if there is any message that has not been caught. If there is, output the list of commands 
    #which have not been parsed so that the user knows what didn't work
    for individual_message in message_parts_list:
        if individual_message.isspace() or (individual_message == ""):
            message_parts_list.remove(individual_message)
    if len(message_parts_list) > 0:
        print("Warning from function config_interpreter: you probably made mistakes in the syntax of some commands. There are commands that you sent and that could not be parsed: {}".format(message_parts_list))

    if len(output_command_list) > 0:
        return output_command_list
    else:    
        print("Message from config_parser: no valid configurations found. Not setting any configurations.")
        output_command_list.append(("nofunction",""))
        return output_command_list

"""
What follows is a list of functions, all written according to similar design strategy and more or less similar implementation
in order to parse the particular string messages and return the output to config interpreter for further processing.
Each of these functions has to be called in EXACTLY the same way as the key in config_command_dictionary, and it takes two arguments:
    input_pattern_raw_string, which is the value corresponding to the key that gives function name in config_command_dictionary, and
    the second argument is message_parts_list, which is just the semicolon-separated list of strings that comes after config; string
In this way, new configurations can be added smoothly by just adding to the dictionary config_command_dictionary, and then defining 
the corresponding function below
"""
def process_cleardata(input_pattern_raw_string,message_parts_list):
    full_Cleardata_pattern = r"({:s})\s+(all|\d{{1,}}\s*)".format(input_pattern_raw_string)
    for individual_message in message_parts_list:
        search_res = re.search(full_Cleardata_pattern,individual_message)
        if search_res:
           message_parts_list.remove(individual_message) # That's just so that if we already found something
           #we don't use it in any further searches
           return ("clear_data",search_res.group(2))
    return None

def process_setAxisLabels(input_pattern_raw_string,message_parts_list):
    full_SetAxislabels_pattern = r"({:s})\s+(.*)".format(input_pattern_raw_string)
    for individual_message in message_parts_list:
        search_res = re.search(full_SetAxislabels_pattern,individual_message)
        if search_res:
            axisLabels = search_res.group(2)
            each_axis_label = axisLabels.split(",")
            if len(each_axis_label) == 2:
                message_parts_list.remove(individual_message)
                return ("set_axis_labels",each_axis_label)
            else:
                print("Message from function process_setAxisLabels: set_axis_labels argument must be two strings separated by a comma. Command must be of the form: set_axis_labels myFavorite X name , myFavorite Y name; Now it's not in that form. Not labeling axes")
    return None

def process_setPlotTitle(input_pattern_raw_string,message_parts_list):
    full_SetPlotTitle_pattern = r"({:s})\s+(.*)".format(input_pattern_raw_string)
    for individual_message in message_parts_list:
        search_res = re.search(full_SetPlotTitle_pattern,individual_message)
        if search_res:
            plottitle = search_res.group(2)
            message_parts_list.remove(individual_message)
            return ("set_plot_title",plottitle)
    return None

def process_setPlotLegend(input_pattern_raw_string,message_parts_list):
    full_SetPlotLegend_pattern = r"({:s})\s+(.*)".format(input_pattern_raw_string)
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

def process_setFitFunction(input_pattern_raw_string,message_parts_list):
    full_SetFitFunction_pattern = r"({:s})\s+(.*)".format(input_pattern_raw_string)
    for individual_message in message_parts_list:
        search_res = re.search(full_SetFitFunction_pattern ,individual_message)
        if search_res:
            fitfunction_name = search_res.group(2).strip() #use strip() in order to remove any possible leading and trailing whitespace
            message_parts_list.remove(individual_message)
            return ("set_fit_function",fitfunction_name)
    return None

def process_setCurveNumber(input_pattern_raw_string,message_parts_list):
    full_SetCurveNumber_pattern = r"({:s})\s+(.*)".format(input_pattern_raw_string)
    for individual_message in message_parts_list:
        search_res = re.search(full_SetCurveNumber_pattern,individual_message)
        if search_res:
            curvenumber_str = search_res.group(2).strip()
            message_parts_list.remove(individual_message)
            return ("set_curve_number",curvenumber_str)
    return None

def process_setStartingParameters(input_pattern_raw_string,message_parts_list):
    full_SetStartingParameters_pattern = r"({:s})\s+(.*)".format(input_pattern_raw_string)
    for individual_message in message_parts_list:
        search_res = re.search(full_SetStartingParameters_pattern,individual_message)
        if search_res:
            output_startparam_dict = {}
            full_startparam_string = search_res.group(2).strip()
            startparam_string_split = full_startparam_string.split(",")
            for singleparam_string in startparam_string_split:
                key_val_pair = singleparam_string.split(":") # key and value are supposed to be separated by a colon
                if (len(key_val_pair) != 2):
                    print("Message from file {:s} function process_setStartingParameters: you tried to set this parameter {} but the format is not parameter : value. Ignoring it".format(__file__,key_val_pair))
                    continue
                else: 
                    key = key_val_pair[0].strip()
                    val = key_val_pair[1].strip()
                    output_startparam_dict[key] = val
            message_parts_list.remove(individual_message)
            return ("set_starting_parameters",output_startparam_dict)
    return None

def process_doFit(input_pattern_raw_string,message_parts_list):
    full_SetDoFit_pattern = r"({:s})\s+".format(input_pattern_raw_string)
    for individual_message in message_parts_list:
        search_res = re.search(full_SetDoFit_pattern,individual_message)
        if search_res:
            return ("do_fit","")
    return None

if __name__ == "__main__":
    pass
