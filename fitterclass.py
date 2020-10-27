# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 16:19:51 2020

@author: Oleksiy
"""
import numpy as np
import scipy as sp
import pandas as pd 
import os
import pyqtgraph as pg
import mathfunctions.fitmodels as mdl
import scipy.optimize as sopt
from PyQt5 import QtWidgets 
from PyQt5 import QtGui, QtCore
import helperfunctions
from inspect import getfullargspec # this is for checking out which arguments are defined in a given function 


#TODELETE
#import matplotlib.pyplot as plt

class GeneralFitter1D:
    def __init__(self,fitmodel):
        self.fitmodel_input = fitmodel
        self.isSetupFitSuccessful = True
        self.optimizer = sopt.least_squares
        """
        All inputs must be either 1D lists or 1D numpy arrays, not anything else. errorbars must be either 1D list or 1D numpy array, or left as none, in which case it will simply be initialized to an array filled with all 1. 
        the __init__ function checks that all inputs are as specified, and returns None if there is any error involved
        """
    
    # TODO Get this to work in order to use different possible 
    #scipy fitting routines
    def setupFit(self,**kwargs):
        """
        Here we establish and (ideally) check all the options to be sent to the fitting method. We give all those options as keyword arguments.
        """
        errorExists = False
        #kwargs_list = ["fitfunction","fitroutine","fitmethod"]
        kwargs_list = []
        function_name = None
        self.isSetupFitSuccessful = False
        self.fitmodel_input.fit_isdone = False # If we call setup fit, it means that we are redoing a fit. It is thus not done yet. This should be reflected here

        key = "fitroutine" # This could be least squares, or things like differential evolution, etc.
        if key in kwargs:
            kwargs_list.append(key)
            if kwargs[key] in ["least_squares","leastsq","lsq"]:
                self.optimizer = sopt.least_squares
            else:
                print("Error: incorrect value for {:s} in setupFit. Fitting impossible".format(key))
                errorExists = True
                return False
        else:
            print("Argument {:s} is not given in setupFit. Assume that the fit routine is scipy.optimize.least_squares".format(key))
            self.optimizer = sopt.least_squares

        key = "fitmethod"
        if key in kwargs:
            kwargs_list.append(key)
            if kwargs[key] in ["lm","levenberg_marquardt"]:
                self.optimizer_method = "lm" # see scipy.optimize.least_squares
            elif kwargs[key] in ["trf"]:
                self.optimizer_method = "trf"
        for key in list(kwargs.keys()):
            if key not in kwargs_list:
                print("Warning: wrong keyword argument {:s} given in setupFit. Ignoring it".format(key))
        
        print("Keys into setupFit: \n", kwargs_list)
        if errorExists:
            return False
        else:
            self.isSetupFitSuccessful = True
            return True

    def doFit(self):
        
        self.fitmodel_input.fit_isdone = False # If we call doFit, it means that we are redoing a fit. It is thus not done yet. This should be reflected here
        if not self.isSetupFitSuccessful:
            print("Message from Class {:s} function doFit: function setupFit in the same class was not successful. Fitting impossible".format(self.__class__.__name__))
            return None

        self.fitmodel_input.do_prefit() # This will refresh all the bounds based on 
        #the inputs in the prefit dialog, and also do the prefit itself if there's None
        #as any of the values in the prefit dictionary

        lowerbounds_list = [self.fitmodel_input.fit_function_paramdict_bounds[key][0] for key in self.fitmodel_input.fit_function_paramdict_prefit.keys()]
        upperbounds_list = [self.fitmodel_input.fit_function_paramdict_bounds[key][1] for key in self.fitmodel_input.fit_function_paramdict_prefit.keys()]
        #TODELETE
        print("Prefit paramdict initial input into doFit: ",list(self.fitmodel_input.fit_function_paramdict_prefit.values()))
        optimization_output = self.optimizer(self.fitmodel_input.fit_function,
                list(self.fitmodel_input.fit_function_paramdict_prefit.values()),
                args = (self.fitmodel_input.xvals,
                        self.fitmodel_input.yvals,
                        self.fitmodel_input.errorbars),
                bounds=(lowerbounds_list,upperbounds_list),
                loss="linear",f_scale=1) 
        self.optimizationResult = optimization_output
        if self.optimizationResult.success is True:
            self.fitmodel_input.fit_isdone = True
            self.fitmodel_input.fit_issuccessful = True
            # we first want to fill the dictionary in the model with fit results
            fitmodel_dictkeylist = list(self.fitmodel_input.fit_function_paramdict_prefit.keys())
            for (idx,key) in enumerate(fitmodel_dictkeylist):
                self.fitmodel_input.fit_function_paramdict[key] = self.optimizationResult.x[idx]

            self.fitmodel_input.fit_result_fulloutput = self.optimizationResult
            return True
        else:
            self.fitmodel_input.fit_isdone = False
            self.fitmodel_input.fit_issuccessful = False
            # if the fit is wrong, it makes sense that the fit result output is None
            self.fitmodel_input.fit_result_fulloutput = None
            return False
   
    def __del__(self):
        print("Closing {:s} class instance".format(self.__class__.__name__))

class PrefitterDialog(QtWidgets.QWidget):
    def __init__(self,fitmodel_instance):
        super().__init__()
        self.NUMPOINTS_CURVE = 350
        self.fitmodel = fitmodel_instance

        # not sure here yet...
        self.preplotdotsymbol = "o"
        self.preplotcolorpalette = helperfunctions.colorpalette[self.fitmodel.fit_function_number%len(helperfunctions.colorpalette)] # This is just modulo in colors so that if there are too many plots, they start repeating colors
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
        #out the grid of dictionary names and values for a 
        #particular plot
        for (idx,(key,val)) in enumerate(self.fitmodel.fit_function_paramdict_prefit.items()):
            label = QtGui.QLabel(key)
            field = QtGui.QLineEdit()
            field.setText("{:.06f}".format(val))
            field.textEdited.connect(self.update_paramdict)
            self.datastring_labels.append(label) # the dictionary labels
            self.datastring_fields.append(field)
            controlfields_layout.addWidget(label,idx,0)
            controlfields_layout.addWidget(field,idx,1)

        dialoglayout.addLayout(controlfields_layout)
        self.setLayout(dialoglayout)
        
        # datapointsplot stands for just the data 
        self.datapointsplot = self.graphWidget1.plot(symbol = self.preplotdotsymbol,
                symbolBrush = self.preplotsymbolbrush,
                pen = pg.mkPen(None))
        self.datapointsplot.setData(self.fitmodel.xvals,
                self.fitmodel.yvals)
        if self.fitmodel.areErrorbarsGiven:
            self.errorbars_plot = pg.ErrorBarItem(x = self.fitmodel.xvals,y=self.fitmodel.yvals,
                    top = self.fitmodel.errorbars,
                    bottom = self.fitmodel.errorbars,
                    pen  = pg.mkPen(color = self.preplotcolorpalette,
                        style = QtCore.Qt.DashLine))
            self.graphWidget1.addItem(self.errorbars_plot)
        
        # curveplot is the plot of the actual curve with whatever
        #prefit parameters are in there at the moment
        self.plotcurve = self.graphWidget1.plot(pen = pg.mkPen(self.preplotcolorpalette,
            style = QtCore.Qt.SolidLine))

        self.makeplot()

    def makeplot(self):
        if None in list(self.fitmodel.fit_function_paramdict_prefit.values()):
            pass
        else:
            paramlist = list(self.fitmodel.fit_function_paramdict_prefit.values())
            aXvalsDense = np.linspace(self.fitmodel.xvals[0],self.fitmodel.xvals[-1],self.NUMPOINTS_CURVE)
            # NOTE! This is not necessarily good, I just assume here that dictionary order does not change. This may be wrong
            aYvalsDense = self.fitmodel.fit_function_base(paramlist,aXvalsDense)
            self.plotcurve.clear()
            self.plotcurve.setData(aXvalsDense,aYvalsDense)

    def update_paramdict(self,atext):

        # we go though the list of the data fields and check what 
        #the new values are and set them into the prefit dictionary
        for idx in range(len(self.datastring_labels)):
            try:
                input_float = float(self.datastring_fields[idx].text())
                self.fitmodel.fit_function_paramdict_prefit[self.datastring_labels[idx].text()] = input_float
            except:
                if (self.datastring_fields[idx].text() == "") or self.datastring_fields[idx].text().isspace():
                    self.fitmodel.fit_function_paramdict_prefit[self.datastring_labels[idx].text()] = None
                else:
                    print("Message from Class {:s}: input value {} in Prefit dialog cannot be converted to float. Clearing the value".format(self.__class__.__name__,
                        self.datastring_fields[idx].text()))
        if None in list(self.fitmodel.fit_function_paramdict_prefit.values()):
            pass
        else:
            self.makeplot()

if __name__ == "__main__":
    columns_to_fit = [4]
    fitter1 = PhononFitter(path="./testdata/ProbCorrByIon.dat")
    fitter1.setFitColumns(columns_to_fit)
    fitter1.readData()
    fitter1.cropData([0,3e-5])

    fitter1.plotOnlyData(linestyle="")
    fitter1.setupFit(fitfunction="damped_sine",initialparams = [2.e5,0.5,0,0.5,0.00001],errorbars_exist=True)
    res = fitter1.doFit()
    print(res.x)
    print(res.success)
    fitter1.plotWithFit()
    #fitter1.setSkipInitRow(5)
    
    
    
    
    
    #import pyqtgraph.examples
    #pyqtgraph.examples.run()
