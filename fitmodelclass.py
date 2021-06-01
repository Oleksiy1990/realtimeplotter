# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 14:39:39 2020

@author: Oleksiy

Writing the function definition for fit models in least squares optimization
We need to find the way to import these functions smartly, either by their normal function names, or possibly
with string versions of their names, and then getattr() and so on
"""

import numpy as np
import math
import mathfunctions.fitmodels as fitmodels
import itertools

class Fitmodel:

    MAX_ERROR_RESOLUTION = 1e20 # 1 over this is the smallest error bar that is considered physical, if it's less, it's considered 0 and so unphysical
    def __init__(self,fitfunction_name = "",
                 #fitfunction_number = -1, #Not quite sure what this is
                 x_axis_vals = [],
                 measured_data = [],
                 errorbars_data = None):
        #input data
        self.fitfunction_name_string = fitfunction_name
        #self.fit_function_number = fitfunction_number
        self.xvals_orig = x_axis_vals
        self.yvals_orig = measured_data
        self.errorbars_orig = errorbars_data
        self.are_errorbars_correct = True
        self.are_errorbars_given = False
        self.monte_carlo_inputs = {}
        self.monte_carlo_startparams = []

        # this gets automatically loaded in order to make it available
        self.start_paramdict = getattr(fitmodels,self.fitfunction_name_string+"_paramdict")()
        self.start_bounds_paramdict = getattr(fitmodels, self.fitfunction_name_string + "_paramdict")()

        # this loads the dictionaries again, but now for storing the fit parameters
        self.result_paramdict = getattr(fitmodels, self.fitfunction_name_string + "_paramdict")()
        # the next one is for fit uncertainties, but it will not be used for now
        #self.result_bounds_paramdict = getattr(fitmodels, self.fitfunction_name_string + "_paramdict")()
        self.result_fulloutput = None
        self.result_objectivefunction = -1

        self.crop_bounds_list = [-math.inf,math.inf] # this is to make the treatment uniform,
        #anyway is infinity beyond any real number
        self.minimization_method_str = "least_squares"
        self.fitter_options_dict = {}

        self.is_fit_done = False
        self.is_fit_successful = False
        self.are_correct_data_loaded = False
        self.xvals = None
        self.yvals = None
        self.errorbars = None

    def preprocess_data(self) -> bool:
        """
        Preprocessor to make sure that the given x_values, y_values, and errorbars are given in the correct format, have the same length,and then
        eventually to turn them all into 1D numpy arrays. Also this makes sure that if error bars are not given, they are just set to 1, which
        makes sense for fitting

        The output is SORTED!

        We need to make the following checks on the data:
        1) legal lists of x and y values. We check it here, we check only that the lengths
        match, we don't check if the lists contain any nonsense, like a non-number.
        It's assumed that such data is not sent, and if it is, it should be filtered out
        in the main file
        2) legal errorbars list or None. If there is the errorbars list, then it should
        be of the same length as x and y values
        3) legal fit function name


        """
        # First we try to convert the data into numpy arrays, and if it fails, we
        # return False
        try:
            self.xvals_orig = np.array(self.xvals_orig)
            self.yvals_orig = np.array(self.yvals_orig)

            # make sure that error bars are correctly formatted, have the correct length, etc
            if self.errorbars_orig is None:
                self.areErrorbarsGiven = False
                self.are_errorbars_correct = True
                self.errorbars_orig = np.ones(self.xvals_orig.shape, dtype=float)
            else:
                self.errorbars_orig = np.array(self.errorbars_orig)
                #TODELETE
                #print(np.any(self.errorbars_orig <= np.abs(self.errorbars_orig)/self.MAX_ERROR_RESOLUTION))
                if np.any(self.errorbars_orig <= np.abs(self.errorbars_orig)/self.MAX_ERROR_RESOLUTION): # this means that at least one of the errors is 0
                    #TODELETE
                    print("from fitmodelclass preprocess_data: we detected at least one zero errorbar")
                    self.are_errorbars_correct = False
                    self.errorbars_orig = np.ones(self.xvals_orig.shape, dtype=float)
        except:
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "preprocess_data"))
            print(
                "Preprocessing failed. Apparently something could not be converted into numpy arrays \n")
            return False

        # check if fit function name is legal (so defined in our file)
        if not hasattr(fitmodels,self.fitfunction_name_string):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "preprocess_data"))
            print("Fit model is not in fitmodels.py file, so such fit model is undefined. Not fitting anything. You provided this fitmodeL: {} \n".format(self.fitmodel_input))
            return False

        # check if the data are legal =========
        if len(self.xvals_orig) < 2 or len(self.yvals_orig) < 2:
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "preprocess_data"))
            print("Your x-values and y-values must have length at least 2 to try any fits. Not fitting anything \n")
            return False
        if len(self.xvals_orig) != len(self.yvals_orig):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "preprocess_data"))
            print("Your x and y values must have the same length. Not fitting anything \n")
            return False
        if len(self.errorbars_orig) != len(self.xvals_orig):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "preprocess_data"))
            print("You provided a list of error bar values, but they are not the same length as your x-values. Not fitting anything")
            return False
        # ===== If we made it to here, then our data are legal =======
        self._sort_xaxis()
        self._do_cropping() # we always do cropping because even if there are no bounds
        # we artificially set bounds to infinity,
        # just because we want to keep it uniform
        # this produces self.xvals, self.yvals, self.errorbars
        #self._remove_zero_errorbars() # this was for correcting errorbars, but not in use now

        # check again if we didn't crop out all the data
        if len(self.xvals) < 2 or len(self.yvals) < 2:
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "preprocess_data"))
            print("Your x-values and y-values must be at least 2 units long. Now it's not the case, you probably cropped out everything. Not fitting anything")
            return False

        return True  # if we got to this point, there is no error, so we can return True

    def _sort_xaxis(self):
        """
        Sorts data by the indices of the x-axis, so that basically x[0] is the leftmost coordinate value, and x[-1] is the rightmost coordinate value
        """
        xaxis_indices = np.argsort(self.xvals_orig)
        self.xvals_orig = self.xvals_orig[xaxis_indices]
        self.yvals_orig = self.yvals_orig[xaxis_indices]
        self.errorbars_orig = self.errorbars_orig[xaxis_indices]

    def _do_cropping(self) -> None:
        crop_x_mask = (self.xvals_orig >= self.crop_bounds_list[0]) & (self.xvals_orig <= self.crop_bounds_list[1])
        # make copies in order to always keep the old one available if necessary
        self.xvals = self.xvals_orig[crop_x_mask].copy()
        self.yvals = self.yvals_orig[crop_x_mask].copy()
        self.errorbars = self.errorbars_orig[crop_x_mask].copy()

    def _remove_zero_errorbars(self) -> None:
        # NOTE!!! This replaces small errorbars by mean of all errorbars
        mean_errorbars = np.mean(self.errorbars)
        stddev_errorbars = np.std(self.errorbars)

        self.errorbars[(self.errorbars < (mean_errorbars - stddev_errorbars)) | (self.errorbars < 1e-10)] = mean_errorbars


    def do_prefit(self) -> bool: 
        """
        self.start_paramdict and self.start_bounds_paramdict are filled in here 
        And if it's all correct, the function returns True, otherwise False
        """

        if (self.xvals is None) or (self.yvals is None) or (self.errorbars is None):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "do_prefit"))
            print("Your xvals, yvals, or errorbars are not set. You probably have not preprocessed data. Not possible to do fit this way")
            return False

        self._do_cropping() # this also resets the input values in case they were modified by the prefitter for example. This is relevant for things like smoothing

        if self._check_start_paramdict_isfull() is True:
            return True

        # If the check above returned False, that means that we have to automatically fill in some
        # starting parameters, and so we do that using the "model"_prefit function from fitmodels.py
        is_prefit_successful = getattr(fitmodels,self.fitfunction_name_string+"_prefit")(self.xvals,
                                                                  self.yvals,
                                                                  self.errorbars,
                                                                  self.start_paramdict,
                                                                  self.start_bounds_paramdict)
        
        if is_prefit_successful:
            return True
        else:
            return False
            
    def fill_in_montecarlo_startparams(self) -> bool:
        if not self.monte_carlo_inputs: # this means that there are no Monte Carlo startparams to consider
            return True
            
        single_param_dict = {}
        # First we fill in uniformly sampled values for each parameter
        # Number of samples is given by the values in the Monte Carlo inputs dictionary
        for (key,value) in self.monte_carlo_inputs.items(): # remember that self.monte_carlo_inputs gives the parameter names to vary and how many random points to take of each
            fitlimits = self.start_bounds_paramdict[key]
            #TODELETE
            #print("Monte Carlo routine. Requested parameter: {}, limits for this parameter: {}".format(key,fitlimits))
            # we will now fill in the temporary ditionary with the lists of random values for each requested parameter
            single_param_dict[key] = [np.random.uniform(*fitlimits) for q in range(value)]
            
        # whichever parameters are not fed into the Monte Carlo, we assume that they will have the values 
        # corresponding to the start_paramdict value
        for otherkey in self.start_paramdict.keys():
            if otherkey not in single_param_dict.keys():
                single_param_dict[otherkey] = [self.start_paramdict[otherkey]]
        # TODELETE
        #print("Monte Carlo routine. Printing the dict with requested parameter lists for Monte Carlo: {}".format(single_param_dict))

        mcdict = {}
        result_combos = list(itertools.product(*single_param_dict.values()))
        #TODELETE
        #print("Monte Carlo combos: {}".format(result_combos))
        for combo in result_combos:
            # we fill in the dictionary with one particular set of initial parameters, based on a given combo
            for (idx,key) in enumerate(single_param_dict.keys()):
                mcdict[key] = combo[idx]
            # now we append it to the list of dictionaries that will be used in fitting
            self.monte_carlo_startparams.append(mcdict.copy()) # Important to copy, otherwise it's only a reference
        #TODELETE
        #print("Monte Carlo startparamsdicts: {}".format(self.monte_carlo_startparams))
        return True
    
    
    def _check_start_paramdict_isfull(self) -> bool:
        """
        Check if the starting parameters have been fully filled. If so, we will
        not need to run the prefit function
        """
        for value in self.start_paramdict.values():
            if value is None: 
                return False
        for value in self.start_bounds_paramdict.values():
            if value is None:
                return False
        return True

    # =============== Not sure if all these functions below will be necessary. This has to be checked later
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








