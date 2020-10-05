# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 14:39:39 2020

@author: Oleksiy

Writing the function definition for fit models in least squares optimization
We need to find the way to import these functions smartly, either by their normal function names, or possibly
with string versions of their names, and then getattr() and so on
"""

import numpy as np
import mathfunctions.fitmodels as fitmodels

class Fitmodel:
    def __init__(self,fitfunction_name,fitfunction_number,x_axis_vals,measured_data,errorbars_in = None):
        
        self.fitfunction_name_string = fitfunction_name
        self.fit_function_number = fitfunction_number
       
        #print("Globals in the file containing Fitmodel: ",fitmodels)
        if not hasattr(fitmodels,self.fitfunction_name_string):
            print("Message from Class {}: fit function {} is undefined, not doing anything".format(self.__class__.__name__,self.fitfunction_name_string))
            return None
       
        datacheck_result = self.checkandsetData(x_axis_vals,measured_data,errorbars_in) # this will preprocess the data to be then used in the fitter
        if not datacheck_result:
            print("Message from Class: data check failed. See earlier error messages, some array formatting, lengths, etc, was not fed correctly. Not doing anything")
        
            # if data check was OK, we will now have three member arrays: 
        
        self.sortDataByXaxis() # now all the arrays are sorted so that self.xvals goes form small to large
    
        self.fit_function_base = getattr(fitmodels,self.fitfunction_name_string+"_base")
        self.fit_function = getattr(fitmodels,self.fitfunction_name_string)

        self.fit_function_params_list = list(getattr(fitmodels,self.fitfunction_name_string+"_paramdict")().keys())
        self.fit_function_paramdict = getattr(fitmodels,self.fitfunction_name_string+"_paramdict")()
        self.fit_function_paramdict_prefit = getattr(fitmodels,self.fitfunction_name_string+"_paramdict")()
        self.fit_function_paramdict_bounds = getattr(fitmodels,self.fitfunction_name_string+"_paramdict")()

        self.do_prefit()
    
    def check_paramdict_isfull(self):
        for value in self,fit_function_paramdict.values():
            if value is None: 
                return False
        return True

    def clear_paramdict_all(self):
        self.fit_function_params_list = list(getattr(fitmodels,self.fitfunction_name_string+"_paramdict")().keys())
        self.fit_function_paramdict = getattr(fitmodels,self.fitfunction_name_string+"_paramdict")()
        self.fit_function_paramdict_prefit = getattr(fitmodels,self.fitfunction_name_string+"_paramdict")()
        self.fit_function_paramdict_bounds = getattr(fitmodels,self.fitfunction_name_string+"_paramdict")()
    
    def clear_paramdict_prefit(self):
        self.fit_function_paramdict_prefit = getattr(fitmodels,self.fitfunction_name_string+"_paramdict")()
        self.fit_function_paramdict_bounds = getattr(fitmodels,self.fitfunction_name_string+"_paramdict")()
    
    def set_prefit_parameter(self,parameter_name,parameter_value):
        if parameter_name in self.fit_function_paramdict_prefit:
            self.fit_function_paramdict_prefit[parameter_name] = parameter_value
        else:
            print("Message from function set_prefit_parameter: parameter name does not exist in the dictionary for the function in use. Not doing anything")
    
    def delete_prefit_parameter(self,parameter_name):
        if parameter_name in self.fit_function_paramdict_prefit:
            self.set_prefit_parameter(parameter_name,None)
        else:
            print("Message from function delete_prefit_parameter: parameter name foes not exist in the dictionary for the function in use. Not doing anything")

    def do_prefit(self,**kwargs):
        prefit_function = getattr(fitmodels,self.fitfunction_name_string+"_prefit")
        (self.fit_function_paramdict_prefit,self.fit_function_paramdict_bounds) = prefit_function(self.xvals,self.yvals,self.errorbars,self.fit_function_paramdict_prefit,
            self.fit_function_paramdict_bounds,**kwargs)


        # TODELETE
        print("Message from Fitmodel do_prefit() function: ", self.fit_function_paramdict_prefit)

    def checkandsetData(self,xvals,yvals,errorbars):

        """
        Preprocessor to make sure that the given x_values, y_values, and errorbars are given in the correct format, have the same length,and then 
        eventually to turn them all into 1D numpy arrays. Also this makes sure that if error bars are not given, they are just set to 1, which 
        makes sense for fitting
        """
        
        # make sure that x values are either a list or a numpy array
        if isinstance(xvals,list):
            self.xvals = np.array(xvals)
        elif isinstance(xvals,np.ndarray):
            self.xvals = xvals
        else:
            print("Message from Class {:s} function checkandsetData: xvals must be either a list or a numpy. Initialize it again with the correct input.".format(self.__class__.__name__))
            return False

        # make sure that y values are either a list or a numpy array
        if isinstance(yvals,list):
            self.yvals = np.array(yvals)
        elif isinstance(yvals,np.ndarray):
            self.yvals = yvals
        else:
            print("Message from Class {:s} function checkandsetData: yvals must be either a list or a numpy. Initialize it again with the correct input.".format(self.__class__.__name__))
            return False
    
        # make sure that x values and y values are both 1D arrays
        if (len(self.xvals.shape) != 1) or (len(self.yvals.shape) != 1):
            print("Message from Class {:s} function checkandsetData: both xvals and yvals arrays must be 1D. Initialize it again with the correct input".format(self.__class__.__name__))
            return False
       
        # make sure that the lengths of the x values and y values are equal
        if (self.xvals.shape[0] != self.yvals.shape[0]):
            print("Message from Class {:s} function checkandsetData: length of the xvals and yvals arrays must be the same. Initialize it again with the correct input".format(self.__class__.__name__))
            return False
        
        # make sure that if error bars are not None, then they are either a list or a numpy array
        if errorbars is not None: 
            if not isinstance(errorbars,list) or isinstance(errorbars,np.ndarray):
                print("Message from Class {:s} function checkandsetData: errorbars, if given, must be either a list or a numpy array. Initialize it again with the correct input.".format(self.__class__.__name__))
                return False
        
        # make sure that error bars are correctly formatted, have the correct length, etc 
        if errorbars is None:
            self.areErrorbarsGiven = False
            self.errorbars = np.ones(self.xvals.shape,dtype=float)
        elif isinstance(errorbars,list):
            self.errorbars = np.array(errorbars)
            self.areErrorbarsGiven = True
        elif isinstance(errorbars,np.ndarray):
            self.errorbars = errorbars
            self.areErrorbarsGiven = True
        else:
            print("Message from Class {:s} function checkandsetData: errorbars must be either a list or a numpy, or do not input anything. Initialize it again with the correct input.".format(self.__class__.__name__))
            return False

        if (self.errorbars.shape[0] != self.xvals.shape[0]):
            print("Message from Class {:s} function checkandsetData: length of the errorbars and xvals and yvals arrays must be the same. Initialize it again with the correct input".format(self.__class__.__name__))
            return False
        
        return True # if we got to this point, there is no error, so we can return True

    def sortDataByXaxis(self):
        xaxis_indices = np.argsort(self.xvals)
        self.xvals = self.xvals[xaxis_indices]
        self.yvals = self.xvals[xaxis_indices]
        self.errorbars = self.xvals[xaxis_indices]


