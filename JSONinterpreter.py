# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 14:27:15 2020

@author: Oleksiy
"""

import re
import json
from typing import Union, Optional, Tuple, List, Any

class JSONread():
    """ 
    The internal communication in the package is via lists of tuples, where
    the first element is the function to call, the second element are
    the paramers of that function
    
    """
    jsonrpc2_keys = ["jsonrpc","method","params","id"]
    # method = STRING data, or config, or getresult, or something else
    # params = DICT with keys being for example which function needs to be called or what sort of data it is, and the value is the corresponding 
    # value then

    method_keys = ["doClear","setConfig","addData","doFit","getFitResult","getConfig"]
    # There are the possible values to go with the "method" key in JSON

    """
    Now let's talk about the value to go with the "params" key:
    This value is itself a dictionary, so it will contain a list of 
    keys and values to go with it. So here we are listing the possible 
    keys to become part of the "params" dictionary for each of the 
    "method" keys. 
    
    We are not listing the values to go with eadh of these keys, because
    that can vary, and that will be written in the manual
    """
    # options to put as params keys for doClear method
    doClear_message_keys = ["clearData"]

    # options to put as params keys for setConfig method
    setConfig_message_keys = ["setAxisLabels",
        "setPlotTitle",
        "setPlotLegend"]

    # options to put as params keys for addData method
    addData_message_keys = ["dataPoint","pointList"]

    # options to put as params keys for doFit method
    doFit_message_keys = ["setFitFunction",
        "setCurveNumber",
        "setStartingParameters",
        "setStartingParametersLimits",
        "setCropLimits",
        "setFitMethod",
        "performFitting"]

    # options to put as params keys for getFitResult method
    getFitResult_message_keys = ["curveNumber"]

    # options to put as params keys for getConfig method
    getConfig_message_keys = [] # this is not defined yet

    error_return = [("nofunction","")]


    def __init__(self):
        pass
    
    def parse_JSON_message(self,message: str) -> List[Tuple[str,Optional[Any]]]:
        """
        this takes the JSON-RPC 2.0 conforming string that comes in via TCP/IP
        and processes it in order to call the corresponding functions downstream (like plot, set configurations, fit)

        step 1: check if the string conforms to JSON RPC 2.0 (use helper function for this)
        step 2: check if the method key contains the right value (use helper function for this)
        step 3: build a list with the appropriate commands to send downstream (use helper functions for this)

        if at any step the processing fails, the thing sends error_return defined above downstream. That's just designed to not
        let the program crash, but rather to send a well-defined error input that will be appropriately ignored further

        """
        (success,dictresult) = self.__check_JSON(message)
        if success is False:
            print("Message from Module {:s}, Class {:s} function {:s} :".format(__name__,
                self.__class__.__name__,"parse_JSON_message"))
            print("Your message apparently does not conform to JSON-RPC 2.0 format. Here is the message that you sent, verbatim: {:s}. Sending nofunction downstread".format(message))
            return JSONread.error_return
        if dictresult["method"] not in JSONread.method_keys:
            print("Message from Module {:s}, Class {:s} function {:s} :".format(__name__,
                self.__class__.__name__,"parse_JSON_message"))
            print("Your method key is not known. Here is what you sent {:s} ; here is what is defined {}. Sending nofunction downstream".format(dictresult["method"],JSONread.method_keys))
            return JSONread.error_return

        # note now that for each possible method value, there's a helper function that must be defined below according 
        # to the name convention __parse_<methodvalue>_message

        callable_for_downstream = getattr(self,"_{:s}__parse_{:s}_message".format(self.__class__.__name__,dictresult["method"]))
        result_for_downstream = callable_for_downstream(dictresult)
        return result_for_downstream

    def __check_JSON(self, message: str) -> Tuple[bool,Optional[dict]]:
        message_dictionary = json.loads(message)
        """
        Get a message string in JSON format and check if it conforms with JSON-RPC 2.0 standard
        Return tuple, first element is True/False, second element is dictionary parsed from JSON
        """
        # first we check that everything conforms to json_prc 2.0 standard
        if set(message_dictionary.keys()) != set(JSONread.jsonrpc2_keys):
            return (False,None)
        elif message_dictionary["jsonrpc"] != "2.0":
            return (False,None)
        elif not isinstance(message_dictionary["method"],str):
            return (False,None)
        elif not isinstance(message_dictionary["params"],dict):
            return (False,None)
        elif not isinstance(message_dictionary["id"],int):
            return (False,None)
        else:
            return (True,message_dictionary)

    def __message_key_to_function_name(self, keystring: str) -> str:
        """
        This function replaces uppercase letters by lowercase ones 
        and inserts an underscore before each letter that used to be 
        uppercase
        """
        newstring = ""
        for letter in keystring:
            if letter.isupper():
                newstring += "_"
                newstring += letter.lower()
            else:
                newstring += letter

        return newstring

    def __parse_doClear_message(self,messagedict: dict) -> List[Tuple[str,Any]]:
        """
        We want to output a list of tuples. The first element in each tuple is the 
        function to call in the program, the second element is whatever is supposed 
        to be fed into that function

        NOTE! Checks params in the exact sequence as defined in doClear_message_keys list
        """
        params_dict = messagedict["params"] # the input that came via JSON
        output = [] # The output list of tuples that will be returned
        for keystring in JSONread.doClear_message_keys: # check out the list of all possible keys to config
            if keystring in params_dict.keys():
                data = params_dict[keystring]
                output.append((self.__message_key_to_function_name(keystring),data))
                params_dict.pop(keystring)
        if not output: # this will evaluate to False if output is empty 
            print("Message from Module {:s}, Class {:s} function {:s} :".format(__name__,
                self.__class__.__name__,"__parse_doClear_message"))
            print("Parsed doClear message is empty. Calling nofunction")
            output = JSONread.error_return
        if params_dict: # this will evaluate to True if params_dict is not empty
            print("Message from Module {:s}, Class {:s} function {:s} :".format(__name__,
                self.__class__.__name__,"__parse_doClear_message"))
            print("There were keys sent via JSON in params dictionary that are not understood. Here's that was not understood: {}".format(list(params_dict.keys())))
        return output
    
    def __parse_setConfig_message(self,messagedict: dict) -> List[Tuple[str,Any]]:
        """
        Get the parsed message dictionary from JSON message and create the message
        that can be sent for further processing (list of tuples, first element being string 
        denoting the funcion name to be called in the program, second element being the data
        to go into that function)
        
        This particular function is for config messages, so we look at the list config_message_keys 
        because it lists in the correct order all possible messages that can make part of config in this program

        Produce warnings if there is no message to send further or if there are params in
        JSON string which do not match any known parameters

        NOTE! Checks params in the exact sequence as defined in setConfig_message_keys list
        """
        params_dict = messagedict["params"] # the input that came via JSON
        output = [] # The output list of tuples that will be returned
        for keystring in JSONread.setConfig_message_keys: # check out the list of all possible keys to config
            if keystring in params_dict.keys():
                data = params_dict[keystring]
                output.append((self.__message_key_to_function_name(keystring),data))
                params_dict.pop(keystring)
        if not output: # this will evaluate to False if output is empty 
            print("Message from Module {:s}, Class {:s} function {:s} :".format(__name__,
                self.__class__.__name__,"__parse_setConfig_message"))
            print("Parsed configuration message is empty. Calling nofunction")
            output = JSONread.error_return
        if params_dict: # this will evaluate to True if params_dict is not empty
            print("Message from Module {:s}, Class {:s} function {:s} :".format(__name__,
                self.__class__.__name__,"__parse_setConfig_message"))
            print("There were keys sent via JSON in params dictionary that are not understood. Here's that was not understood: {}".format(list(params_dict.keys())))
        return output
    
    def __parse_addData_message(self,messagedict: dict) -> List[Tuple[str,Any]]:
        """
        This particular function is for data messages, so we look at the list data_message_keys 
        because it lists in the correct order all possible messages that can make part of data in this program

        Produce warnings if there is no message to send further or if there are params in
        JSON string which do not match any known parameters
        
        Note! This does not check params in the exact sequence as defined in addData_message_keys
        """
        params_dict = messagedict["params"] # the input that came via JSON
        #output = [] # The output list of tuples that will be returned
        
        # here we check that we didn't pass any keys that do not conform to what's known to the program for data
        # we delete any key that is not listed in data_message_keys
        for key in params_dict.keys(): 
            if key not in JSONread.addData_message_keys:
                print("Message from Module {:s}, Class {:s} function {:s} :".format(__name__,
                    self.__class__.__name__,"__parse_addData_message"))
                print("method data got unknown parameter key: {}. Deleting that key".format(key))
                params_dict.pop(key)

        if len(params_dict) != 1: # note that here it must be exactly one entry in the params dictionary
            print("Message from Module {:s}, Class {:s} function {:s} :".format(__name__,
                self.__class__.__name__,"__parse_addData_message"))
            print("Got a number of entries into params dictionary that is different from 1. Not doing anything, you must provide a single key-value pair")
            return JSONread.error_return
       
        if params_dict.get("dataPoint"): # if this evaluates to True, is means that this key is given, so we are sending a single data point
            #TODO: Define plot_single_datapoint
            return [("plot_single_datapoint",params_dict["dataPoint"])]
        elif params_dict.get("pointList"):
            return [("plot_single_datapoint",single_dict) for single_dict in params_dict["pointList"]]
        else:
            print("Something is really strange in Module {:s}; we should not have come to this line".format(__name__))
            return JSONread.error_return

    def __parse_doFit_message(self,messagedict: dict) -> List[Tuple[str,Any]]:
        params_dict = messagedict["params"]  # the input that came via JSON
        output = []  # The output list of tuples that will be returned
        for keystring in JSONread.doFit_message_keys:  # check out the list of all possible keys to config
            if keystring in params_dict.keys():
                data = params_dict[keystring]
                output.append((self.__message_key_to_function_name(keystring), data))
                params_dict.pop(keystring)
        if not output:  # this will evaluate to False if output is empty
            print("Message from Module {:s}, Class {:s} function {:s} :".format(__name__,
                                                                                self.__class__.__name__,
                                                                                "__parse_doFit_message"))
            print("Parsed configuration message is empty. Calling nofunction")
            output = JSONread.error_return
        if params_dict:  # this will evaluate to True if params_dict is not empty
            print("Message from Module {:s}, Class {:s} function {:s} :".format(__name__,
                                                                                self.__class__.__name__,
                                                                                "__parse_doFit_message"))
            print(
                "There were keys sent via JSON in params dictionary that are not understood. Here's that was not understood: {}".format(
                    list(params_dict.keys())))
        return output

    def __parse_getFitResult_message(self,messagedict: dict) -> List[Tuple[str,Any]]:
        params_dict = messagedict["params"]  # the input that came via JSON
        output = []  # The output list of tuples that will be returned
        for keystring in JSONread.getFitResult_message_keys:  # check out the list of all possible keys to config
            if keystring in params_dict.keys():
                data = params_dict[keystring]
                output.append(("get_fit_result", data))
                params_dict.pop(keystring)
        if not output:  # this will evaluate to False if output is empty
            print("Message from Module {:s}, Class {:s} function {:s} :".format(__name__,
                                                                                self.__class__.__name__,
                                                                                "__parse_getFitResult_message"))
            print("Parsed configuration message is empty. Calling nofunction")
            output = JSONread.error_return
        if params_dict:  # this will evaluate to True if params_dict is not empty
            print("Message from Module {:s}, Class {:s} function {:s} :".format(__name__,
                                                                                self.__class__.__name__,
                                                                                "__parse_getFitResult_message"))
            print(
                "There were keys sent via JSON in params dictionary that are not understood. Here's that was not understood: {}".format(
                    list(params_dict.keys())))
        return output


def message_interpreter_twoway(message_in = ""):
    """
    Note: this parses the incoming message into the two-way communication
    """
    if len(message_in) == 0:
        print("Function message_interpreter_twoway: apparently no message received, length of message string is 0. Not doing anything")
        return (False,"nomessage",)
    
    message = message_in.strip() # get rid of any possible whitespaces before and after
    message_in_split = message.split(";") #
    start_command = message_in_split[0].strip()
    if start_command == "getfitparams":
        curve_str = message_in_split[1].strip()
        try:
            curve = int(curve_str)
        except:
            print("Message from message_interpreter_twoway: you put in this curve number: {}. It is not an integer. Ignoring it".format(curve_str))
            return (False,"curvenotaninteger",)
        return (True,"",curve)

    else:
        return (False,"wrongcommand",)

# I just deleted message_interpreter
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
        "process_doFit" : r"dofit|doFit|do_fit",
        "process_setCropTuple": r"setCropTuple|set_crop_tuple"}

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
                individual_label_pattern_curvenums = r"(curve|Curve)(\d{1,2})\s+(.*)"
                individual_label_search_res_curvenums = re.search(individual_label_pattern_curvenums,legendlabel)
                if individual_label_search_res_curvenums: # TODO: Implement this well
                    curve_num = int(individual_label_search_res_curvenums.group(2))
                    legend_string = individual_label_search_res_curvenums.group(3)
                    legend_labels_list.append((curve_num,legend_string))
                else:
                    legend_labels_list.append(legendlabel.strip())

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
            # Next line means: different parameters are supposed to be separated by a comma
            startparam_string_split = full_startparam_string.split(",")

            for singleparam_string in startparam_string_split:
                # Next line means: key and value are supposed to be separated by a colon
                key_val_pair = singleparam_string.split(":") 
                if (len(key_val_pair) != 2):
                    print("Message from file {:s} function process_setStartingParameters: you tried to set this parameter {} but the format is not parameter : value. Ignoring it".format(__file__,key_val_pair))
                    continue
                else: 
                    key = key_val_pair[0].strip()
                    val = key_val_pair[1].strip()
                try:
                    val_float = float(val)
                    output_startparam_dict[key] = val_float
                except:
                    print("Message from Module {} function process_setStartingParameter: in entry {}:{} the value {} cannot be converted to float. Not adding this to output dictionary".format(__name__,key,val,val))
            message_parts_list.remove(individual_message)
            return ("set_starting_parameters",output_startparam_dict)
    return None

def process_setCropTuple(input_pattern_raw_string,message_parts_list):
    """
    For now we only set the crop tuples for the fitting purposes, not for the plotting purposes
    One is supposed to give a command of the form "setCropTuple 5e-3, 15e-3;" or something like that
    One can also use None if one of the sides should have no crop bound.
    """
    full_SetCropTuple_pattern = r"({:s})\s+(.*)".format(input_pattern_raw_string)
    for individual_message in message_parts_list:
        search_res = re.search(full_SetCropTuple_pattern,individual_message)
        if search_res:
            curvenumber_str = search_res.group(2).strip()
            crop_bounds_str_list = curvenumber_str.split(",")
            try:
                leftbound = float(crop_bounds_str_list[0].strip())
            except:
                if crop_bounds_str_list[0].strip() != "None":
                    print("Message from file {} function process_setCropTuple: the left bound is not a number and not None. Ignoring it and setting it to None".format(
                        __name__))
                leftbound = None
            try:
                rightbound = float(crop_bounds_str_list[1].strip())
            except:
                if crop_bounds_str_list[1].strip() != "None":
                    print("Message from file {} function process_setCropTuple: the right bound is not a number and not None. Ignoring it and setting it to None".format(
                        __name__))
                rightbound = None
            message_parts_list.remove(individual_message)
            return ("set_crop_tuple",(leftbound,rightbound))
    return None

def process_doFit(input_pattern_raw_string,message_parts_list):
    full_SetDoFit_pattern = r"({:s})\s*".format(input_pattern_raw_string)
    for individual_message in message_parts_list:
        search_res = re.search(full_SetDoFit_pattern,individual_message)
        if search_res:
            message_parts_list.remove(individual_message)
            return ("do_fit","")
    return None

if __name__ == "__main__":
    pass
