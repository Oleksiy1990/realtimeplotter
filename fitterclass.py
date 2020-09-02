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


class GeneralFitter1D:
    def __init__(self,xvals=None,yvals=None,errorbars=None):
        """
        All inputs must be either 1D lists or 1D numpy arrays, not anything else. errorbars must be either 1D list or 1D numpy array, or left as none, in which case it will simply be initialized to an array filled with all 1. 
        the __init__ function checks that all inputs are as specified, and returns None if there is any error involved
        """
        
        self.okToFit = False
        
        if errorbars is not None: 
            if not isinstance(errorbars,list) or isinstance(errorbars,np.ndarray):
                print("Message from class {:s}: errorbars, if given, must be either a list or a numpy array. Initialize it again with the correct input.".format(self.__class__.__name__))
                return None

        if isinstance(xvals,list):
            self.xvals = np.array(xvals)
        elif isinstance(xvals,np.ndarray):
            self.xvals = xvals
        else:
            print("Message from class {:s}: xvals must be either a list or a numpy. Initialize it again with the correct input.".format(self.__class__.__name__))
            return None
        if isinstance(yvals,list):
            self.yvals = np.array(yvals)
        elif isinstance(yvals,np.ndarray):
            self.yvals = yvals
        else:
            print("Message from class {:s}: yvals must be either a list or a numpy. Initialize it again with the correct input.".format(self.__class__.__name__))
            return None

        if (len(self.xvals.shape) != 1) or (len(self.yvals.shape) != 1):
            print("Message from class {:s} both xvals and yvals arrays must be 1D. Initialize it again with the correct input".format(self.__class__.__name__))
            return None
        
        if (self.xvals.shape[0] != self.yvals.shape[0]):
            print("Message from class {:s}: length of the xvals and yvals arrays must be the same. Initialize it again with the correct input".format(self.__class__.__name__))
            return None
        
        if errorbars is None:
            self.errorbars = np.ones(self.xvals.shape,dtype=float)
        elif isinstance(errorbars,list):
            self.errorbars = np.array(errorbars)
        elif isinstance(errorbars,np.ndarray):
            self.errorbars = errorbars
        else:
            print("Message from class {:s}: errorbars must be either a list or a numpy, or do not input anything. Initialize it again with the correct input.".format(self.__class__.__name__))
            return None

        if (self.errorbars.shape[0] != self.xvals.shape[0]):
            print("Message from class {:s}: length of the errorbars and yvals arrays must be the same. Initialize it again with the correct input".format(self.__class__.__name__))
            return None
        self.okToFit = True


        #NOTE! self.xvals is not sorted in this case!

    def cropData(self,cropping_bounds = None):
        if not self.okToFit:
            print("Warning message from Class {:s} function cropData: okToFit parameter is False. Something was wrong with the data you provided, check previous error messages. Not cropping".format(self.__class__.__name__))
            return None
        if cropping_bounds is None:
            print("Warning message from Class {:s} function cropData: you did not provide cropping bounds. Function cannot be applied".format(self.__class__.__name__))
            return None
        if isinstance(cropping_bounds,list):
            cropping_bounds_numpy = np.array(cropping_bounds)
        elif isinstance(cropping_bounds,np.ndarray):
            cropping_bounds_numpy = cropping_bounds
        else: 
            print("Message from class {:s} function cropData: croppings bounds must be either a list or a 1D numpy array. Not cropping")
            return None
        if (len(cropping_bounds_numpy.shape) != 1) or (cropping_bounds_numpy.shape[0] != 2):
            print("Message from class {:s} function cropData: croppings bounds must a 1D list or array of length = 2. Not cropping")
            return None

        # The cropping procedure itself
        self.xvals = self.xvals[self.xvals > cropping_bounds_numpy[0]]
        self.xvals = self.xvals[self.xvals < cropping_bounds_numpy[1]]
        self.yvals = self.yvals[self.xvals > cropping_bounds_numpy[0]]
        self.yvals = self.yvals[self.xvals < cropping_bounds_numpy[1]]
        self.errorbars = self.errorbars[self.xvals > cropping_bounds_numpy[0]]
        self.errorbars = self.errorbars[self.xvals < cropping_bounds_numpy[1]]

    def setupFit(self,**kwargs):
        """
        Here we establish and (ideally) check all the options to be sent to the fitting method. We give all those options as keyword arguments.
        """
        errorExists = False
        #kwargs_list = ["fitfunction","fitroutine","fitmethod"]
        kwargs_list = []
        function_name = None
        self.isSetupFitSuccessful = False


        key = "fitfunction" # this is just the mathematical function that has to be fitted
        if key in kwargs:
            kwargs_list.append(key)
            if kwargs[key] in ["sine","sinewave","sinusoidal"]:
                function_name = "sinewave"
            elif kwargs[key] in ["damped_sine","decay_sine","damped_sinusoidal"]:
                function_name = "damped_sinewave"
            else: 
                print("Error: incorrect value for {:s} in setupFit. Fitting impossible".format(key))
                errorExists = True
                return False
        else:
            print("Argument {:s} is not given in setupFit. Fitting impossible".format(key))
            errorExists = True
            return False
        self.fitfunction = getattr(mdl,function_name+"_e")
        self.fitfunctionBase = getattr(mdl,function_name+"_base")
        

        key = "initialparams" # this must be a list in the correct form 
        self.initialparams = None
        init_param_generator = getattr(mdl,function_name+"_prefit")
        init_param_generator_result = init_param_generator(self.xvals,self.yvals,self.errorbars)
        if key in kwargs:
            kwargs_list.append(key)
            check_func = getattr(mdl,function_name + "_check")
            try:
                check_init_param = check_func(kwargs[key])
                if check_init_param:
                    self.initialparams = np.array(kwargs[key])
                    self.params_bounds = np.array(init_param_generator_result[1])
            except TypeError:
                print("Warning from setupFit: Initial parameters to fit function {:s} are not a list. Ignoring given initial parameters and using automatically generated ones".format(function_name))
                self.initialparams = np.array(init_param_generator_result[0])
                self.params_bounds = np.array(init_param_generator_result[1])
        if self.initialparams is None:
            print("Note from setupFit: no initial parameters given, using prefit to automatically generate initial parameters")
            self.initialparams = np.array(init_param_generator_result[0])
            self.params_bounds = np.array(init_param_generator_result[1])

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
        if not self.okToFit:
            print("Message from Class {:s} function doFit: okToFit is false. No fitting".format(self.__class__.__name__))
            return None
        if not self.isSetupFitSuccessful:
            print("Message from Class {:s} function doFit: function setupFit in the same class was not successful. Fitting impossible".format(self.__class__.__name__))
            return None
        optimization_output = self.optimizer(self.fitfunction,self.initialparams,
                args = (self.xvals,self.yvals,self.errorbars),
                bounds=(self.params_bounds[:,0],self.params_bounds[:,1]),
                loss="linear",f_scale=1) 
        self.optimizationResult = optimization_output
        return optimization_output
   

    def plotFit(self,pyqtgraph_plotwidget,linestyle = "--"):
        aXvalsDense = np.linspace(np.min(self.xvals),np.max(self.xvals),350)
        print("from plotFit: x[0] :",aXvalsDense[0])
        print("from plotFit: x[-1] :",aXvalsDense[-1])
        pyqtgraph_plotwidget.plot(aXvalsDense,self.fitfunctionBase(self.optimizationResult.x,aXvalsDense),pen="k")

    
    def __del__(self):
        print("Closing {:s} class instance".format(self.__class__.__name__))


class PhononFitter:
    """
    Define so that it makes a single fit, one data set
    Take data from absolute path for now
    """
    
    def __init__(self,path = None,fitcolumns=None):
        
        self.__zeroerror_correction = [1e-10,1e10] # this is now only hard-coded in this way! Maybe we need a function to be able to change it
        self.__skip_init_row = False
        self.__path_unchecked = path
        self.FitColumns = None
        self.dataAvailable = False
        self.optimizationResults = []

        if self.FitColumns is None:
            print("Class {:s} constructor message: FitColumns attribute is None. Use setFitColumns() and then readData()".format(self.__class__.__name__))
            return None
        self.setFitColumns(fitcolumns)
        self.readData(path)
        if not self.dataAvailable:
            print("Class {:s} constructor message: could not import data. Check path, then feed it into readData()".format(self.__class__.__name__))
            return None
        
        #print(self.independent_variable)
        #print(len(self.dependent_variables))
        #print(len(self.error_bars))
        #print(self.df.head(2))
        #print(self.df.columns)
    
    def setSkipInitRow(self,bool_val=False):
        if bool_val is True:
            self.__skip_init_row = True 
        elif bool_val is False:
            self.__skip_init_row = False
        else:
            print("Error in input parameter class {:s}".format(self.__class__.__name__))

    def setFitColumns(self,fitcolumns):
        if type(fitcolumns) is int:
            result = np.array([fitcolumns])
            self.FitColumns = result
        elif type(fitcolumns) is list:
            result = np.array(fitcolumns)
            typecheck_int = np.all(result.dtype is np.dtype(int))
            if typecheck_int:
                self.FitColumns = result
            else:
                print("Function setFitColumns message: You put non-integer column values in setFitColumns. Setting columns_tofit to None ")
                self.FitColumns = None 
        else:
            print("setFitColumns function: not correct column numbers to fit. Setting to None")
            self.FitColumns = None  

    def readData(self,path = None):
        if path is None: 
            myPath = self.__path_unchecked
        else: 
            myPath = path
            self.__path_unchecked = myPath
        isPath = os.path.isfile(myPath)
        if not isPath:
            print("Initialization class {:s}: Not given correct path to data file in function readData. Fitting impossible".format(self.__class__.__name__))
            self.dataAvailable = False
            return False

        try:
            col_list_length = len(self.FitColumns)
            if col_list_length < 1:
                print("Length of FitColumns is less than 1. You must specify at least one data column to fit. Fitting impossible")
                self.dataAvailable = False
                return False
        except:
            print("Cannot determine the length of the FitColumns attribute. You should supply a valid list of integers to specify which columns to fit. Fitting impossible")
            self.dataAvailable = False
            return False
        
        self.optimizationResults = [] #reset the optimization result to empty if we are going to load another dataset
        df = pd.read_csv(myPath,sep="\t",comment="#",header=None)
        if self.__skip_init_row:
            df.drop(self.df.head(1).index,inplace=True)
        
        self.independent_variable = df.iloc[:,0].values
        self.dependent_variables = []
        self.error_bars = []
        df_numcolumns = df.shape[1]
        for data_col_idx in self.FitColumns:
            if data_col_idx < 1:
                print("Message from readData. You assigned an invalid data column value: {:d}. The smallest possible data column is 1. Fitting impossible".format(data_col_idx))
                self.dataAvailable = False
                return False
            if (data_col_idx + 1) >= df_numcolumns:
                print("Message from readData. You assigned an invalid data column value: {:d}. The largest possible data columns value is {:d}. Fitting impossible".format(data_col_idx,df_numcolumns - 2))
                self.dataAvailable = False
                return False
            values_single_array = df.iloc[:,data_col_idx].values
            self.dependent_variables.append(values_single_array)
            error_bars_single_array = df.iloc[:,data_col_idx+1].values
            error_bars_single_array[error_bars_single_array < self.__zeroerror_correction[0]] = self.__zeroerror_correction[1]
            self.error_bars.append(error_bars_single_array) #We are always supposed to have the error bar in the next column after the data values

        self.dataAvailable = True
        return True

    def cropData(self,cropping_bounds = None):
        if not self.dataAvailable:
            print("Warning message from Class {:s} function cropData: there is no data available. Function cannot be applied".format(self.__class__.__name__))
            return None
        if cropping_bounds is None:
            print("Warning message from Class {:s} function cropData: you did not provide cropping bounds. Function cannot be applied".format(self.__class__.__name__))
            return None
        if isinstance(cropping_bounds,list) or isinstance(cropping_bounds,np.ndarray):
            if len(cropping_bounds) == 2:
                boolean_mask = np.where((self.independent_variable > cropping_bounds[0]) & (self.independent_variable < cropping_bounds[1]))
                crop_try = self.independent_variable[boolean_mask]
                if crop_try.shape[0] == 0:
                    print("Warning message from Class {:s} function cropData: no data left after cropping. No cropping will be done".format(self.__class__.__name__))
                    return None

                self.independent_variable = crop_try
                for idx,dep_var_arr in enumerate(self.dependent_variables):
                    self.dependent_variables[idx] = dep_var_arr[boolean_mask]
                for idx,error_bar_arr in enumerate(self.error_bars):
                    self.error_bars[idx] = error_bar_arr[boolean_mask]
            else:
                print("Warning message from Class {:s} function cropData: Cropping bounds must be an array of two numbers. No cropping".format(self.__class__.__name__))
                return None
            

    def setupFit(self,**kwargs):
        """
        Here we establish and (ideally) check all the options to be sent to the fitting method. We give all those options as keyword arguments.
        """
        errorExists = False
        #kwargs_list = ["fitfunction","fitroutine","fitmethod"]
        kwargs_list = []
        function_name = None
        self.isSetupFitSuccessful = False


        key = "fitfunction" # this is just the mathematical function that has to be fitted
        if key in kwargs:
            kwargs_list.append(key)
            if kwargs[key] in ["sine","sinewave","sinusoidal"]:
                function_name = "sinewave"
            elif kwargs[key] in ["damped_sine","decay_sine","damped_sinusoidal"]:
                function_name = "damped_sinewave"
            else: 
                print("Error: incorrect value for {:s} in setupFit. Fitting impossible".format(key))
                errorExists = True
                return False
        else:
            print("Argument {:s} is not given in setupFit. Fitting impossible".format(key))
            errorExists = True
            return False

        key = "initialparams"
        check_init_param = False
        if key in kwargs:
            kwargs_list.append(key)
            check_func = getattr(mdl,function_name + "_check")
            try:
                check_init_param = check_func(kwargs[key])
            except TypeError:
                print("Warning from setupFit: Initial parameters to fit function {:s} are not a list. Ignoring initial parameters".format(function_name))
                check_init_param = False
        if check_init_param:
            self.initialparams = kwargs[key]
        else:
            self.initialparams = None
            print("Message from setupFit: no initial parameters given for the fit with fit function {:s}".format(function_name))


        key = "errorbars_exist"
        if key in kwargs:
            kwargs_list.append(key)
            if kwargs[key] is True: 
                self.fitfunction = getattr(mdl,function_name+"_e")
                self.fitfunctionBase = getattr(mdl,function_name+"_base")
                self.doErrorbarsExist = True
            elif kwargs[key] is False: 
                self.fitfunction = getattr(mdl,function_name)
                self.fitfunctionBase = getattr(mdl,function_name+"_base")
                self.doErrorbarsExist = False
            else: 
                print("Error: incorrect value for {:s} in setupFit. Fitting impossible".format(key))
                errorExists = True
                return False
        else: 
            print("Warning: no option for error bars given in setupFit. Fitting without error bars")
            self.fitfunction = getattr(mdl,function_name)
            self.fitfunctionBase = getattr(mdl,function_name+"_base")
            self.doErrorbarsExist = False



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
        if not self.dataAvailable:
            print("Message from Class {:s} function doFit: no data available for fitting".format(self.__class__.__name__))
            return None
        if not self.isSetupFitSuccessful:
            print("Message from Class {:s} function doFit: function setupFit in the same class was not successful. Fitting impossible".format(self.__class__.__name__))
            return None
        if (self.initialparams is not None) and self.doErrorbarsExist:
            optimization_output = self.optimizer(self.fitfunction,self.initialparams,
                    args = (self.independent_variable,self.dependent_variables[0],self.error_bars[0]),loss="linear",f_scale=1) 
            self.optimizationResults.append(optimization_output)
            return optimization_output
        elif (self.initialparams is not None) and (self.doErrorbarsExist is False):
            optimization_output = self.optimizer(self.fitfunction,self.initialparams,
                    args = (self.independent_variable,self.dependent_variables[0]),loss="linear",f_scale=1) 
            self.optimizationResults.append(optimization_output)
            return optimization_output

        else:
            print("No initial parameters given, no fitting now")
            pass

    def plotWithFit(self,linestyle = "--"):
        if len(self.optimizationResults) == 0: # this means that there is no fit result available 
            print("Error message Class {:s} function plotWithFit: optimization result is not available. Plotting with fit impossible".format(self.__class__.__name__))
            return None
        import matplotlib.pyplot as plt
        mpl_colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
       
        # The next check is just for smoothness of plotting
        if self.independent_variable.shape[0]<300:
            x_axis_points = np.linspace(self.independent_variable[0],self.independent_variable[-1],300)
        else:
            x_axis_points = self.independent_variable

        for idx in range(len(self.optimizationResults)):
            optimization_output_params = self.optimizationResults[idx].x
            plt.errorbar(self.independent_variable,self.dependent_variables[idx], yerr =self.error_bars[idx],marker = ".", linestyle = "",color = mpl_colors[idx])
            plt.plot(x_axis_points,self.fitfunctionBase(optimization_output_params,x_axis_points),linestyle = linestyle,color = mpl_colors[idx])
        plt.ylim((-0.1,1.1))
        plt.show()
        plt.close()


    def plotOnlyData(self,linestyle = ""):
        """
        This is purely to plot the data that we feed to the fitter. No fits made here
        """
        if not self.dataAvailable: 
            print("Message from Class {:s} function plotOnlyData: no data to plot. Plotting impossible".format(self.__class__.__name__))
            return None
        if self.FitColumns is None: 
            print("Message from function plotOnlyData: Data columns have not been specified. Plotting impossible")
            return None
        import matplotlib.pyplot as plt
        for idx in range(len(self.dependent_variables)):
            plt.errorbar(self.independent_variable,self.dependent_variables[idx], yerr = self.error_bars[idx],marker = ".", linestyle = linestyle)
        plt.ylim((-0.1,1.1))
        plt.show()
        plt.close()




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
