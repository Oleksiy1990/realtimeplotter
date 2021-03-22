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
#import fitmodels


# TODELETE
# import matplotlib.pyplot as plt

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
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "setup_fit"))
            print(
                "You provided a minimization method that is not in scipy.optimize library. Not fitting anything \n")
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
    def __init__(self, fitmodel_instance):
        super().__init__()
        self.NUMPOINTS_CURVE = 350
        self.fitmodel = fitmodel_instance

        # not sure here yet...
        self.preplotdotsymbol = "o"
        self.preplotcolorpalette = helperfunctions.colorpalette[self.fitmodel.fit_function_number % len(
            helperfunctions.colorpalette)]  # This is just modulo in colors so that if there are too many plots, they start repeating colors
        self.preplotsymbolbrush = pg.mkBrush(self.preplotcolorpalette)

        # set window title, layout, and pyqtgraph plotting widget
        self.setWindowTitle("Pre-fit dialog")
        dialoglayout = QtWidgets.QVBoxLayout()
        self.graphWidget1 = pg.PlotWidget()
        self.graphWidget1.setBackground('w')
        dialoglayout.addWidget(self.graphWidget1)
        controlfields_layout = QtWidgets.QGridLayout()
        self.datastring_fields = []
        self.datastring_labels = []

        # Here we set up the prefit GUI by filling 
        # out the grid of dictionary names and values for a
        # particular plot
        for (idx, (key, val)) in enumerate(self.fitmodel.fit_function_paramdict_prefit.items()):
            label = QtGui.QLabel(key)
            field = QtGui.QLineEdit()
            field.setText("{:.06f}".format(val))
            field.textEdited.connect(self.update_paramdict)
            self.datastring_labels.append(label)  # the dictionary labels
            self.datastring_fields.append(field)
            controlfields_layout.addWidget(label, idx, 0)
            controlfields_layout.addWidget(field, idx, 1)

        dialoglayout.addLayout(controlfields_layout)
        self.setLayout(dialoglayout)

        # datapointsplot stands for just the data 
        self.datapointsplot = self.graphWidget1.plot(symbol=self.preplotdotsymbol,
                                                     symbolBrush=self.preplotsymbolbrush,
                                                     pen=pg.mkPen(None))
        self.datapointsplot.setData(self.fitmodel.xvals,
                                    self.fitmodel.yvals)
        if self.fitmodel.areErrorbarsGiven:
            self.errorbars_plot = pg.ErrorBarItem(x=self.fitmodel.xvals, y=self.fitmodel.yvals,
                                                  top=self.fitmodel.errorbars,
                                                  bottom=self.fitmodel.errorbars,
                                                  pen=pg.mkPen(color=self.preplotcolorpalette,
                                                               style=QtCore.Qt.DashLine))
            self.graphWidget1.addItem(self.errorbars_plot)

        # curveplot is the plot of the actual curve with whatever
        # prefit parameters are in there at the moment
        self.plotcurve = self.graphWidget1.plot(pen=pg.mkPen(self.preplotcolorpalette,
                                                             style=QtCore.Qt.SolidLine))

        self.makeplot()

    def makeplot(self):
        if None in list(self.fitmodel.fit_function_paramdict_prefit.values()):
            pass
        else:
            paramlist = list(self.fitmodel.fit_function_paramdict_prefit.values())
            aXvalsDense = np.linspace(self.fitmodel.xvals[0], self.fitmodel.xvals[-1], self.NUMPOINTS_CURVE)
            # NOTE! This is not necessarily good, I just assume here that dictionary order does not change. This may be wrong
            aYvalsDense = self.fitmodel.fit_function_base(paramlist, aXvalsDense)
            self.plotcurve.clear()
            self.plotcurve.setData(aXvalsDense, aYvalsDense)

    def update_paramdict(self, atext):

        # we go though the list of the data fields and check what 
        # the new values are and set them into the prefit dictionary
        for idx in range(len(self.datastring_labels)):
            try:
                input_float = float(self.datastring_fields[idx].text())
                self.fitmodel.fit_function_paramdict_prefit[self.datastring_labels[idx].text()] = input_float
            except:
                if (self.datastring_fields[idx].text() == "") or self.datastring_fields[idx].text().isspace():
                    self.fitmodel.fit_function_paramdict_prefit[self.datastring_labels[idx].text()] = None
                else:
                    print(
                        "Message from Class {:s}: input value {} in Prefit dialog cannot be converted to float. Clearing the value".format(
                            self.__class__.__name__,
                            self.datastring_fields[idx].text()))
        if None in list(self.fitmodel.fit_function_paramdict_prefit.values()):
            pass
        else:
            self.makeplot()

