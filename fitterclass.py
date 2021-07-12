# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 16:19:51 2020

@author: Oleksiy
"""
import numpy as np
import scipy as sp
# import pandas as pd
import os
import pyqtgraph as pg
from fitmodelclass import Fitmodel
import mathfunctions.fitmodels as fitmodels
import scipy.optimize as sopt
from PyQt5 import QtWidgets
from PyQt5 import QtGui, QtCore
import helperfunctions
from inspect import getfullargspec  # this is for checking out which arguments are defined in a given function
from functools import partial
import types
#import fitmodels


# Here we define the additional fit methods that are not in scipy.optimize
# This allows us to define basically whatever we want along the same interface
ADDITIONAL_FITMETHODS = ["findmax","findmin" # this is for peak finding
        ]

# This is a utility function in order to get immediately sum squares for optimizers other than 
# scipy.optimize.least_squares
def sum_squares_decorator(model_function):
    def inner(*args, **kwargs):
        result = model_function(*args, **kwargs)
        sum_squares = 0.5 * np.sum(np.square(result))  # the factor 0.5 is there to just make it
        # exactly the same as the expression in scipy.optimize.least_squares
        return sum_squares

    return inner


class GeneralFitter1D:
    def __init__(self, fitmodel: Fitmodel):
        self.fitmodel_input = fitmodel
        self.is_setup_fit_successful = False

        self.opt_method_string_name = ""
        self.dict_to_optimizer = {}

        """
        All inputs must be either 1D lists or 1D numpy arrays, not anything else. errorbars must be either 1D list or 1D numpy array, or left as none, in which case it will simply be initialized to an array filled with all 1. 
        the __init__ function checks that all inputs are as specified, and returns None if there is any error involved
        """

    # TODO Get this to work in order to use different possible fitting routines
    def setup_fit(self) -> bool:
        """
        TODO: comments here

        """
        # Note: self.fitmodel_input is the instance of class Fitmodel that we use here
        # do preprocessing and check if that succeeds
        is_preprocessing_good = self.fitmodel_input.preprocess_data()
        if is_preprocessing_good is False:
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "setup_fit"))
            print("Preprocessing failed \n")
            return False

        # check if minimization method is legal from the point of view of scipy.optimize
        if not hasattr(sopt, self.fitmodel_input.minimization_method_str):
            if self.fitmodel_input.minimization_method_str in ADDITIONAL_FITMETHODS:
                # TODELETE
                print("From Class {:s} function {:s}".format(self.__class__.__name__, "setup_fit"))
                print("Note: your fit method is not from scipy.optimize library")
            else:
                print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "setup_fit"))
                print(
                    "You provided a minimization method that is not in scipy.optimize library and not among your ADDITIONAL_FITMETHODS. Not fitting anything \n")
                return False

        is_prefit_good = self.fitmodel_input.do_prefit()
        if is_prefit_good is True:
            self.is_setup_fit_successful = True
            self.fitmodel_input.fill_in_montecarlo_startparams() # If there is no input for Monte Carlo, this will do nothing
            
            # Defaults: opt_method is "least-squares" and dict_to_optimizer = {}
            #self.opt_method_string_name = opt_method
            #self.dict_to_optimizer = dict_to_optimizer
            return True
        else:
            return False
            
    def _helper_run_appropriate_fitter(self,lowerbounds_list: list,
                                       upperbounds_list: list,
                                       bounds_not_least_squares: sopt.Bounds): 
        """
        We start with an instance of Fitmodel class, which is saved as 
        self.fitmodel_input
        This instance has the necessary data to run the fit, including the appropriate 
        fit method string name

        Return: optimization output or None
        depending on whether the fit was successful or not
        """
                
        if self.fitmodel_input.minimization_method_str == "least_squares":
            fit_function_callable = getattr(fitmodels,self.fitmodel_input.fitfunction_name_string)
            optimization_output = sopt.least_squares(fit_function_callable,
                                                      np.array(list(self.fitmodel_input.start_paramdict.values())),
                                                      args=(self.fitmodel_input.xvals,
                                                            self.fitmodel_input.yvals,
                                                            self.fitmodel_input.errorbars),
                                                      bounds=(lowerbounds_list, upperbounds_list),
                                                      loss="linear", f_scale=1)
            return optimization_output
        elif self.fitmodel_input.minimization_method_str == "minimize":
            fit_function_callable = getattr(fitmodels,self.fitmodel_input.fitfunction_name_string)
            optimization_output = sopt.minimize(sum_squares_decorator(fit_function_callable),
                                                np.array(list(self.fitmodel_input.start_paramdict.values())),
                                                args=(self.fitmodel_input.xvals,
                                                      self.fitmodel_input.yvals,
                                                      self.fitmodel_input.errorbars),
                                                bounds=bounds_not_least_squares,
                                                **self.fitmodel_input.fitter_options_dict)
            return optimization_output
        elif self.fitmodel_input.minimization_method_str == "basinhopping":
            fit_function_callable = getattr(fitmodels, self.fitmodel_input.fitfunction_name_string)
            optimization_output = sopt.basinhopping(
                sum_squares_decorator(fit_function_callable),
                np.array(list(self.fitmodel_input.start_paramdict.values())),
                minimizer_kwargs = {"args":(self.fitmodel_input.xvals,
                      self.fitmodel_input.yvals,
                      self.fitmodel_input.errorbars),
                                    "method":"trust-constr"}, # TODO: figure out a smart thing to use here
                **self.fitmodel_input.fitter_options_dict)
            # The next lines is just for now the weirdness of basinhopping, it doesn't
            # have the global attribute called success
            setattr(optimization_output,"success",optimization_output.lowest_optimization_result.success)
            return optimization_output
        elif self.fitmodel_input.minimization_method_str == "differential_evolution":
            fit_function_callable = getattr(fitmodels, self.fitmodel_input.fitfunction_name_string)
            optimization_output = sopt.differential_evolution(
                sum_squares_decorator(fit_function_callable),
                bounds_not_least_squares,
                args=(self.fitmodel_input.xvals,
                      self.fitmodel_input.yvals,
                      self.fitmodel_input.errorbars),
            **self.fitmodel_input.fitter_options_dict)
            return optimization_output
        elif self.fitmodel_input.minimization_method_str == "shgo":
            fit_function_callable = getattr(fitmodels, self.fitmodel_input.fitfunction_name_string)
            optimization_output = sopt.shgo(
                sum_squares_decorator(fit_function_callable),
                tuple(zip(lowerbounds_list,upperbounds_list)),
                args=(self.fitmodel_input.xvals,
                      self.fitmodel_input.yvals,
                      self.fitmodel_input.errorbars),
            **self.fitmodel_input.fitter_options_dict)
            return optimization_output
        elif self.fitmodel_input.minimization_method_str == "dual_annealing":
            fit_function_callable = getattr(fitmodels, self.fitmodel_input.fitfunction_name_string)
            optimization_output = sopt.dual_annealing(
                sum_squares_decorator(fit_function_callable),
                tuple(zip(lowerbounds_list,upperbounds_list)),
                args=(self.fitmodel_input.xvals,
                      self.fitmodel_input.yvals,
                      self.fitmodel_input.errorbars),
            **self.fitmodel_input.fitter_options_dict)
            return optimization_output
        elif self.fitmodel_input.minimization_method_str == "findmax":
            # make a copy so that we can go about deleting the max value to find the next
            # max and so on
            peaks_xvals = []
            peaks_yvals = []
            data_array_copy = self.fitmodel_input.yvals.copy()
            # find max, then replace that point with the average, find the next max 
            # and keep going until found as many maxima as requested
            for peak_num in range(self.fitmodel_input.start_paramdict["numpeaks"]):
                peakval_y = np.nanmax(data_array_copy)
                peakcoord = np.argmax(data_array_copy)
                peakval_x = self.fitmodel_input.xvals[peakcoord]
                peaks_xvals.append(peakval_x)
                peaks_yvals.append(peakval_y)
                data_array_copy[peakcoord] = np.mean(data_array_copy)
            # we now have to build the optimization_output object that will look similar to what it looks like for regular fits
            param_dict_length = len(self.fitmodel_input.start_paramdict)
            optimization_output = types.SimpleNamespace() # this just initializes an empty class
            optimization_output.fun = -1 # objective function is -1, because it has no meaning here
            optimization_output.x = [peaks_xvals,peaks_yvals]
            # we now add the values to the "output" which are not real fit parameters
            # in normal fitting these are always fit parameters, but since this is a "fake" fit, we can simply add the initial parameters just to keep the interface constant
            for (idx,key) in enumerate(self.fitmodel_input.start_paramdict):
                if idx >= len(optimization_output.x):
                    optimization_output.x.append(self.fitmodel_input.start_paramdict[key])
            optimization_output.success = True
            return optimization_output
        elif self.fitmodel_input.minimization_method_str == "findmin":
            # make a copy so that we can go about deleting the max value to find the next
            # max and so on
            peaks_xvals = []
            peaks_yvals = []
            data_array_copy = self.fitmodel_input.yvals.copy()
            # find max, then replace that point with the average, find the next max 
            # and keep going until found as many maxima as requested
            for peak_num in range(self.fitmodel_input.start_paramdict["numpeaks"]):
                peakval_y = np.nanmin(data_array_copy)
                peakcoord = np.argmin(data_array_copy)
                peakval_x = self.fitmodel_input.xvals[peakcoord]
                peaks_xvals.append(peakval_x)
                peaks_yvals.append(peakval_y)
                data_array_copy[peakcoord] = np.mean(data_array_copy)
            # we now have to build the optimization_output object that will look similar to what it looks like for regular fits
            param_dict_length = len(self.fitmodel_input.start_paramdict)
            optimization_output = types.SimpleNamespace() # this just initializes an empty class
            optimization_output.fun = -1 # objective function is -1, because it has no meaning here
            optimization_output.x = [peaks_xvals,peaks_yvals]
            for (idx,key) in enumerate(self.fitmodel_input.start_paramdict):
                if idx >= len(optimization_output.x):
                    optimization_output.x.append(self.fitmodel_input.start_paramdict[key])
            optimization_output.success = True
            return optimization_output
        else:
            print(
                """Message from Class {:s} function _helper_run_appropriate_fitter: 
                you tried to use the following optimizer: {}. 
                This optimizer does not exist. Not doing any optimization""".format(
                    self.__class__.__name__, self.fitmodel_input.minimization_method_str))
            return None

    def do_fit(self) -> bool:
        self.fitmodel_input.is_fit_done = False # if we call the fitter, that means that we want a new result, so we should invalidate the old one
        self.fitmodel_input.is_fit_successful = False

        if self.is_setup_fit_successful is False:
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "do_fit"))
            print("Function setup_fit returned False. Check out what's going on there. Fitting impossible")
            return False
        
        # First we generate the lists of bounds to send to the optimizers
        lowerbounds_list = [self.fitmodel_input.start_bounds_paramdict[key][0] for key \
                            in self.fitmodel_input.start_bounds_paramdict]
        upperbounds_list = [self.fitmodel_input.start_bounds_paramdict[key][1] for key \
                            in self.fitmodel_input.start_bounds_paramdict]
        # this one is for optimizers other than least_squares
        bounds_not_least_squares = sopt.Bounds(lowerbounds_list, upperbounds_list)


        opt_output_list = []

        # Here we perform the first fit!
        opt_output_trial = self._helper_run_appropriate_fitter(lowerbounds_list,
                                       upperbounds_list,
                                       bounds_not_least_squares)
                                       
        if self.fitmodel_input.monte_carlo_inputs: # this only runs if Monte Carlo is requested
            print("Monte Carlo fitting runs requested: {:d}".format(len(self.fitmodel_input.monte_carlo_startparams)))
            opt_output_list.append(opt_output_trial)
            idx_mc = 1
            for startparamdict_mc in self.fitmodel_input.monte_carlo_startparams:
                print("Current Monte Carlo iteration: {:d} out of {:d}".format(idx_mc,len(self.fitmodel_input.monte_carlo_startparams)))
                self.fitmodel_input.start_paramdict = startparamdict_mc
                opt_output_trial = self._helper_run_appropriate_fitter(lowerbounds_list,
                                       upperbounds_list,
                                       bounds_not_least_squares)
                opt_output_list.append(opt_output_trial)
                idx_mc += 1
                
            self.fitmodel_input.is_fit_done = True
            # Now we get rid of all failed fits    
            for entry in opt_output_list:
                if entry is None:
                    opt_output_list.remove(entry)
                if entry.success is False:
                    opt_output_list.remove(entry)
            # now we work with this optimization output list
            if len(opt_output_list) < 1: 
                print("Message from Class {:s} function doFit.".format(
                self.__class__.__name__))
                print("No result left in the list of fits after Monte Carlo. Either some error occurred or none of the fits converged") 
                self.fitmodel_input.is_fit_successful = False
                return True # we stop the function here, fit is not successful
            else:
                costfunction_list = np.array([opt_output_list[q].fun for q in range(len(opt_output_list))])
                #TODELETE
                print("Costfunction list: {}".format(costfunction_list))
                min_cost_position = np.argmin(costfunction_list)
                optimization_output = opt_output_list[min_cost_position]
        else:
            optimization_output = opt_output_trial
            self.fitmodel_input.is_fit_done = True

        if optimization_output.success is True:
            self.fitmodel_input.is_fit_successful = True
            # we first want to fill the dictionary in the model with fit results
            fitmodel_dictkeylist = list(self.fitmodel_input.start_paramdict.keys())
            for (idx, key) in enumerate(fitmodel_dictkeylist):
                self.fitmodel_input.result_paramdict[key] = optimization_output.x[idx]
            self.fitmodel_input.result_fulloutput = optimization_output
            if isinstance(optimization_output.fun,(int,float)):
                self.fitmodel_input.result_objectivefunction = optimization_output.fun
            else:
                self.fitmodel_input.result_objectivefunction = optimization_output.fun[0]
        else:
            print("Message from Class {:s} function doFit: apparently the fit did not converge.".format(
                self.__class__.__name__))
            self.fitmodel_input.is_fit_successful = False
        return True

class PrefitterDialog(QtWidgets.QWidget):
    def __init__(self, fitmodel_instance,curvenumber):
        super().__init__()
        self.NUMPOINTS_CURVE = 350
        self.fitmodel = fitmodel_instance       
        is_preprocess_good = fitmodel_instance.preprocess_data()
        if is_preprocess_good:
            is_prefit_good = fitmodel_instance.do_prefit()
        else:
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "__init__"))
            print("Data preprocessing failed. Apparently something was wrong with the data points sent into the fit model. Not doing prefitting \n")
            return None
        if is_prefit_good is False:
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "__init__"))
            print("Prefit failed. Cannot do any further prefitting \n")
            return None
            
        # not sure here yet...
        self.preplotdotsymbol = "o"
        self.preplotcolorpalette = helperfunctions.colorpalette[curvenumber% len(
            helperfunctions.colorpalette)]  # This is just modulo in colors so that if there are too many plots, they start repeating colors
        self.preplotsymbolbrush = pg.mkBrush(self.preplotcolorpalette)

        # set window title, layout, and pyqtgraph plotting widget
        self.setWindowTitle("Prefit dialog")
        dialoglayout = QtWidgets.QVBoxLayout()
        self.prefitGraphWidget = pg.PlotWidget()
        self.prefitGraphWidget.setBackground('w')
        dialoglayout.addWidget(self.prefitGraphWidget)
        controlfields_layout = QtWidgets.QGridLayout()
        self.datastring_fields = []
        self.datastring_labels = []
        # Here we set up the prefit GUI by filling 
        # out the grid of dictionary names and values for a
        # particular plot
        for (line_idx,(key, val)) in enumerate(self.fitmodel.start_paramdict.items()):
            label = QtGui.QLabel(key)
            field = QtGui.QLineEdit()
            field.setText(str("{:.06f}".format(val)))
            field.textEdited.connect(self.update_paramdict)
            self.datastring_labels.append(label)  # the dictionary labels
            self.datastring_fields.append(field)
            controlfields_layout.addWidget(label, line_idx, 0)
            controlfields_layout.addWidget(field, line_idx, 1)

        dialoglayout.addLayout(controlfields_layout)
        self.setLayout(dialoglayout)

        # datapointsplot stands for just the data 
        self.datapointsplot = self.prefitGraphWidget.plot(symbol=self.preplotdotsymbol,
                                                     symbolBrush=self.preplotsymbolbrush,
                                                     pen=pg.mkPen(None))
        self.datapointsplot.setData(self.fitmodel.xvals,
                                    self.fitmodel.yvals)
        if self.fitmodel.errorbars is not None:
            self.errorbars_plot = pg.ErrorBarItem(x=self.fitmodel.xvals, y=self.fitmodel.yvals,
                                                  top=self.fitmodel.errorbars,
                                                  bottom=self.fitmodel.errorbars,
                                                  pen=pg.mkPen(color=self.preplotcolorpalette,
                                                               style=QtCore.Qt.DashLine))
            self.prefitGraphWidget.addItem(self.errorbars_plot)

        # curveplot is the plot of the actual curve with whatever
        # prefit parameters are in there at the moment
        self.plotcurve = self.prefitGraphWidget.plot(pen=pg.mkPen(self.preplotcolorpalette,
                                                             style=QtCore.Qt.SolidLine))

        self.makeplot()

    def makeplot(self):
        paramlist = list(self.fitmodel.start_paramdict.values())
        aXvalsDense = np.linspace(self.fitmodel.xvals[0], self.fitmodel.xvals[-1], self.NUMPOINTS_CURVE)
        # NOTE! This is not necessarily good, I just assume here that dictionary order does not change. This may be wrong
        aYvalsDense = getattr(fitmodels,self.fitmodel.fitfunction_name_string+"_base")(paramlist, aXvalsDense)
        self.plotcurve.clear()
        self.plotcurve.setData(aXvalsDense, aYvalsDense)

    def update_paramdict(self, atext):

        # we go though the list of the data fields and check what 
        # the new values are and set them into the prefit dictionary
        for idx in range(len(self.datastring_labels)):
            # if we deleted everything from some line, then it should not plot anything and wait until we inserted a valid parameter guess
            if self.datastring_fields[idx].text().strip() == "":
                return None
            try:
                input_float = float(self.datastring_fields[idx].text())
                self.fitmodel.start_paramdict[self.datastring_labels[idx].text()] = input_float
                self.makeplot()
            except:
                print(
                    "Message from Class {:s} function update_paramdict".format(self.__class__.__name__))
                print("You typed in value {} as one of the parameters. This is not a numeric input, this is not allowed. Clearing the value \n".format(self.datastring_fields[idx].text()))
                self.datastring_fields[idx].setText("")
