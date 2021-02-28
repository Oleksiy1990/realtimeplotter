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
    setConfig_message_keys = ["axisLabels",
        "plotTitle",
        "plotLegend"]

    # options to put as params keys for addData method
    addData_message_keys = ["dataPoint","pointList"]

    # options to put as params keys for doFit method
    # Order is important!
    doFit_message_keys = [
        "fitFunction",
        "curveNumber", # we feed the data into the Fitmodel instance here
        "startingParameters",
        "startingParametersLimits",
        "cropLimits",
        "fitMethod",
        "fitterOptions",
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
                # output command is message key with all lowercase, underscore_separated
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
                # we have to append this "set_" because that's what the functions are called in the main program
                output.append(("set_"+self.__message_key_to_function_name(keystring),data))
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
                # We have to append "set_" before every function name because that's how
                # it's done in the main program
                output.append(("set_"+self.__message_key_to_function_name(keystring), data))
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

def process_axisLabels(input_pattern_raw_string,message_parts_list):
    full_axisLabels_pattern = r"({:s})\s+(.*)".format(input_pattern_raw_string)
    for individual_message in message_parts_list:
        search_res = re.search(full_axisLabels_pattern,individual_message)
        if search_res:
            axisLabels = search_res.group(2)
            each_axis_label = axisLabels.split(",")
            if len(each_axis_label) == 2:
                message_parts_list.remove(individual_message)
                return ("set_axis_labels",each_axis_label)
            else:
                print("Message from function process_axisLabels: set_axis_labels argument must be two strings separated by a comma. Command must be of the form: set_axis_labels myFavorite X name , myFavorite Y name; Now it's not in that form. Not labeling axes")
    return None

def process_plotTitle(input_pattern_raw_string,message_parts_list):
    full_plotTitle_pattern = r"({:s})\s+(.*)".format(input_pattern_raw_string)
    for individual_message in message_parts_list:
        search_res = re.search(full_plotTitle_pattern,individual_message)
        if search_res:
            plottitle = search_res.group(2)
            message_parts_list.remove(individual_message)
            return ("set_plot_title",plottitle)
    return None

if __name__ == "__main__":
    pass
