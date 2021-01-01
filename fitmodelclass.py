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
        self.fit_isdone = False
        self.fit_issuccessful = False
        self.are_correct_data_loaded = False
        self.xvals_orig = None
        self.yvals_orig = None
        self.errorbars_orig = None

        #print("Globals in the file containing Fitmodel: ",fitmodels)
        if not hasattr(fitmodels,self.fitfunction_name_string):
            print("Message from Class {}: fit function {} is undefined, not doing anything".format(self.__class__.__name__,self.fitfunction_name_string))
            return None
       
        datacheck_result = self.checkandsetData(x_axis_vals,measured_data,errorbars_in) # comes out already sorted!
        if datacheck_result is True:
            self.are_correct_data_loaded = True
        else:
            self.are_correct_data_loaded = False
            print("Message from Class: data check failed. See earlier error messages, some array formatting, lengths, etc, was not fed correctly. Not doing anything")
    
        self.fit_function_base = getattr(fitmodels,self.fitfunction_name_string+"_base")
        self.fit_function = getattr(fitmodels,self.fitfunction_name_string)

        self.fit_function_params_list = list(getattr(fitmodels,self.fitfunction_name_string+"_paramdict")().keys())
        self.fit_function_paramdict = getattr(fitmodels,self.fitfunction_name_string+"_paramdict")()
        self.fit_function_paramdict_prefit = getattr(fitmodels,self.fitfunction_name_string+"_paramdict")()
        self.fit_function_paramdict_bounds = getattr(fitmodels,self.fitfunction_name_string+"_paramdict")()
        self.fit_result_fulloutput = None
        self.fit_result_objectivefunction = None # this hold the value of what had to be minimized, so sum squared of residuals normally

        self.do_prefit()
    
    def check_paramdict_isfull(self):
        for value in self.fit_function_paramdict.values():
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
        """
        Important:
        This is the prefit routine, which fills the prefit parameter dictionary and bounds that will then
        be passed to the fitter itself
        """
        prefit_function = getattr(fitmodels,self.fitfunction_name_string+"_prefit")
        (self.fit_function_paramdict_prefit,self.fit_function_paramdict_bounds) = prefit_function(self.xvals,self.yvals,self.errorbars,self.fit_function_paramdict_prefit,
            self.fit_function_paramdict_bounds,**kwargs)


    def checkandsetData(self,xvals,yvals,errorbars):

        """
        Preprocessor to make sure that the given x_values, y_values, and errorbars are given in the correct format, have the same length,and then 
        eventually to turn them all into 1D numpy arrays. Also this makes sure that if error bars are not given, they are just set to 1, which 
        makes sense for fitting

        The output is unsorted!
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

        self.sortDataByXaxis()  # now the x-axis is sorted!

        # fill the arrays with the original values so that they do not get lost if we try to crop, then crop again
        # with different limits, for example. In general, we may want, after some faulty operation,
        # get back to the original array. This is where that array is stored
        # NOTE! we need to make copies, otherwise the array will be modified in subsequent functions. This is a
        # general property of Python arrays (also Numpy)
        self.xvals_orig = self.xvals.copy()
        self.yvals_orig = self.yvals.copy()
        self.errorbars_orig = self.errorbars.copy()
        return True # if we got to this point, there is no error, so we can return True

    def sortDataByXaxis(self):
        """
        Sorts data by the indices of the x-axis, so that basically x[0] is the leftmost coordinate value, and x[-1] is the rightmost coordinate value
        """
        xaxis_indices = np.argsort(self.xvals)
        self.xvals = self.xvals[xaxis_indices]
        self.yvals = self.yvals[xaxis_indices]
        self.errorbars = self.errorbars[xaxis_indices]

    def do_cropping(self,xmin=None,xmax=None):
        if xmin is None:
            xmin = -1e+100 # that's a random very small number
        if xmax is None:
            xmin = 1e+100  # that's a random very large number
        if self.are_correct_data_loaded is True:
            crop_x_mask = (self.xvals_orig > xmin) & (self.xvals_orig < xmax)
            # make copies in order to always keep the old one available if necessary
            self.xvals = self.xvals_orig[crop_x_mask].copy()
            self.yvals = self.yvals_orig[crop_x_mask].copy()
            self.errorbars = self.errorbars_orig[crop_x_mask].copy()
        else:
            print("Message from Class {} function cropdata: cropping failed according to your x-limits. Check out the limits given".format(
                self.__class__.__name__))


