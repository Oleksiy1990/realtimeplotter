# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 22:34:40 2020

@author: Oleksiy
"""

#import pyqtgraph as pg
#import PyQt5 as Qt
from PyQt5 import QtWidgets, QtCore, QtGui
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import traceback, sys  # We need sys so that we can pass argv to QApplication
import os
from random import randint
import numpy as np
from functools import partial
from socketserver import TCPIPserver
#from interpreter import message_interpreter (that's the old one)
from JSONinterpreter import JSONread
from fitterclass import GeneralFitter1D, PrefitterDialog
import fitmodelclass as fm
import helperfunctions
from typing import Optional, Tuple, List, Any, Union

pg.setConfigOptions(crashWarning=True)

MAX_CURVES = 100 # This is kind of a too large number, just to hard-code the max number of plots that we can have 

class WorkerSignals(QtCore.QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data
    
    error
        `tuple` (exctype, value, traceback.format_exc() )
    
    result
        `object` data returned from processing, anything

    '''
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(tuple)
    request_to_main = QtCore.pyqtSignal(object)
    newdata = QtCore.pyqtSignal(str)

class TCP_IP_Worker(QtCore.QRunnable):
    """
    This is to process TCP/IP requests in Threads
    
    Note that the only thing that this really does is to get a listener function 
    as an argument, it also makes a WorkerSignals() instance, and then it defines a run()
    method, makes it a slot, and when it's called, it passes the WorkerSignals instance to the listener function
    """
    def __init__(self, listener_fn):
        # listener_fn is the function which will be called in the thread
        super().__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = listener_fn
        self.signals = WorkerSignals() # this maybe should actually be passed as an instance
        
    @QtCore.pyqtSlot() # this specifically marks the run() function as a slot
    def run(self): # it looks like this function is called by QtCore.QThreadPool()
        try:
            self.fn(self.signals) 
            # Ok so newdata is the stuff that we feed into the listener function
        except: # Ok this is if something doesn't work, error message
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))

# This class is an example from a tutorial, it is NOT used!
class Worker(QtCore.QRunnable):
    '''
        Worker thread

        Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

        :param callback: The function callback to run on this worker thread. Supplied args and 
                         kwargs will be passed through to the runner.
        :type callback: function
        :param args: Arguments to pass to the callback function
        :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @QtCore.pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(
                *self.args, **self.kwargs
            )
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done

class MainWindow(QtGui.QMainWindow):

    def __init__(self, aTCPIPserver,aTCPIPServerTwoway,is_testing=False):
        if not is_testing:
            super().__init__()

        maxthreads_threadpool = 5
        
        # this is a predefined color palette in order to produce plots, 
        #first line drawn with have the same color on every plot, 
        #same for the second line, and so on
        self.colorpalette = helperfunctions.colorpalette

        # Now we give string-valued names to all the attributes that will have 
        #multiple members during the fitting procedures
        """

        self.yaxis_name : the basis for the attributes that will hold the data
            on the vertical axis (Dependent variable)
        self.err_name : the basis for the attributes that will hold the error values
            bars for each point
        self.plot_line_name : the basis for the plot name, to be used with pyqtgraph
        self.errorbar_item_name : the basis for the objects of type ErrorbarItem"
            that pyqtgraph will use for plotting error bars
        self.pen_name : the basis for style container for the curves in pyqtgraph
        self.errorbar_pen_name : the basis for the style of the error bar marks
        self.fitmodel_instance_name : this is a string holding the name of the fitmodel instance, which will have the data and the fit function in one data structure. 
            we need a fitmodel_instance_name for every curve
        self.fitmethod_name : the name of the fit method to give to scipy.optimize. It could be least_squares, 
            differential_evolution, etc. Check scipy.optimize documentation
        
        """
        self.xaxis_name = "x"
        self.yaxis_name = "y"
        self.err_name = "err"
        self.fit_cropbounds_name = "fitcropbounds"
        self.plot_line_name = "data_line"
        self.fitplot_line_name = "fit_line"
        self.errorbar_item_name = "errorbar_item"
        self.legend_item_name = "legend_item"
        self.pen_name = "pen"
        self.errorbar_pen_name = "errpen"
        self.fitmodel_instance_name = "fitmodel"


        self.fitmethod_string = "differential_evolution"

        self.all_instance_attribute_names = [self.xaxis_name,
                self.yaxis_name,
                self.err_name,
                self.fit_cropbounds_name,
                self.plot_line_name,
                self.fitplot_line_name,
                self.errorbar_item_name,
                self.pen_name,
                self.errorbar_pen_name,
                self.fitmodel_instance_name]

        #self.x = [] # This is the x-axis for all plots
        # NOTE: Maybe we will have to change this so that plots with different 
        #numbers of x-axis points can be processed uniformly 
        self.legend_label_list = []
        self.legend_label_dict = {}

        self.myJSONread = JSONread()

        # This is the number of datasets in the current state of the class instance
        self.num_datasets = 0
        self.arePlotsCleared = True
        self.prefitDialogWindow = None

        if is_testing:
            return None

        #================== Below is the stuff for building the GUI itslef

        # the main window is the one holding the plot, and some buttons below. 
        #we make it a vertical box QVBoxLayout, then in this vertical box structure
        #horizontal boxes can be added for buttons, fields, etc. 
        mainwindow_layout = QtWidgets.QVBoxLayout()
        
        # The main field for plotting, which is taken from pyqtgraph, will be called 
        #graphWidget (instance of pyqtgraph.PlotWidget() )
        self.graphWidget = pg.PlotWidget() 
        self.graphWidget.setBackground('w')

        # we set the legend here. The labels have to be set in the definitions of curves later in the code
        setattr(self, self.legend_item_name, self.graphWidget.addLegend())
        mainwindow_layout.addWidget(self.graphWidget)

        # Two buttons right below the plot: Clear plot and clear data
        self.ClearPlotButton = QtGui.QPushButton("Clear plot")
        self.ClearDataButton = QtGui.QPushButton("Clear data")
        self.ClearPlotButton.clicked.connect(partial(self.clear_plot,""))
        self.ClearDataButton.clicked.connect(partial(self.clear_data,"all"))
        
        ClearPlotAndDataBox = QtGui.QHBoxLayout()
        ClearPlotAndDataBox.addWidget(self.ClearPlotButton)
        ClearPlotAndDataBox.addWidget(self.ClearDataButton)
        mainwindow_layout.addLayout(ClearPlotAndDataBox) # so we can keep adding widgets as we go, they will be added below in vertical box layout, because the main layout is defined to be the vertical box layout
        
       
        # Next row in the GUI: buttons controls related to making the fit
        self.MakeFitButton = QtGui.QPushButton("Do fit")
        self.PrefitButton = QtGui.QPushButton("Prefit")
        self.RegisterCurvesButton = QtGui.QPushButton("Reg. cv.")
        self.RegisterCurvesButton.clicked.connect(self.register_available_curves)
        self.MakeFitButton.clicked.connect(self.process_MakeFit_button)
        self.PrefitButton.clicked.connect(self.process_Prefit_button)
        
        self.FitFunctionChoice = QtGui.QComboBox()
        self.PlotNumberChoice = QtGui.QComboBox()
        self.FitFunctionChoice.addItems(["None","sinewave","damped_sinewave","gaussian"])
        # self.PlotNumberChoice.addItems should be called in the code in order to create a choice which plot to fit 
        MakeFitBoxLayout = QtGui.QHBoxLayout()
        MakeFitBoxLayout.addWidget(self.MakeFitButton)
        MakeFitBoxLayout.addWidget(self.PrefitButton)
        MakeFitBoxLayout.addWidget(self.RegisterCurvesButton)
        MakeFitBoxLayout.addWidget(self.FitFunctionChoice)
        MakeFitBoxLayout.addWidget(self.PlotNumberChoice)
        mainwindow_layout.addLayout(MakeFitBoxLayout)
       
        #First we create a layout into which we will put widgets
        CropBoxLayout =QtGui.QHBoxLayout() 
        #create the widgets themselves, and set their properties
        self.DoCropButton = QtGui.QPushButton("Crop data")
        self.CropLowerLimit = QtGui.QLineEdit()
        self.CropLowerLimit.setAlignment(QtCore.Qt.AlignLeft)
        self.CropLowerLimit.setPlaceholderText("lowlim")
        self.CropUpperLimit = QtGui.QLineEdit()
        self.CropUpperLimit.setAlignment(QtCore.Qt.AlignLeft)
        self.CropUpperLimit.setPlaceholderText("uplim")
        #attach action to crop button
        self.DoCropButton.clicked.connect(self.process_Crop_button)
        #add the widgets to the layout
        CropBoxLayout.addWidget(self.DoCropButton)
        CropBoxLayout.addWidget(self.CropLowerLimit)
        CropBoxLayout.addWidget(self.CropUpperLimit)
        #add layout to the main window
        mainwindow_layout.addLayout(CropBoxLayout) 

        # Text box at the bottom for displaying fit results to the user
        self.TextBoxForOutput = QtGui.QTextEdit()
        self.TextBoxForOutput.setReadOnly(True)
        self.TextBoxForOutput.setFontPointSize(12.)
        mainwindow_layout.addWidget(self.TextBoxForOutput)
        
        # setting the main widget to be the one containing the plot and setting 
        #the main window layout
        mainwidget = QtWidgets.QWidget()
        mainwidget.setLayout(mainwindow_layout)
        #self.setGeometry(50,50,700,700)
        self.setCentralWidget(mainwidget)
        self.show()

        # =======================================
        # TCP/IP Communication, together with Qt Threads
        # This has to do with QT threads, for now this is just following the examples, not sure if this is the best way
        self.threadpool = QtCore.QThreadPool()
        self.threadpool.setMaxThreadCount(maxthreads_threadpool)
        
        # Note that this listener_function_Qt is the one that 
        #has the while True loop to keep listening
        myTCP_IP_Worker = TCP_IP_Worker(aTCPIPserver.listener_function_Qt)
        myTCP_IP_Worker_Twoway = TCP_IP_Worker(aTCPIPServerTwoway.listener_function_Twoway)
        myTCP_IP_Worker.signals.newdata.connect(self.interpret_message)
        myTCP_IP_Worker_Twoway.signals.request_to_main.connect(self.process_fitresults_call)
        self.threadpool.start(myTCP_IP_Worker)
        self.threadpool.start(myTCP_IP_Worker_Twoway)

    ###### End of __init__()

    def interpret_message(self,message: str) -> None:
        """
        Message is supposed to be a string. 
        The result is a list of tuples. Each tuple has the form 
        ("function name",argument)
        """
        if (message == "Done") or (message == ""):
            return None # This is because somehow socketserver.py sends these things.
            # TODO: improve the socket server class

        interpretation_result = self.myJSONread.parse_JSON_message(message)
        # the line above produces a list of tuples form the JSON-RPC message
        # the first element of the tuple is always the string name of the function to call
        # the second element is always the parameter to feed into the function
        for res in interpretation_result:
            function_to_call = getattr(self,res[0],self.nofunction)
            type(function_to_call)
            function_to_call(res[1])
        self.message_processed = True
    
    def process_fitresults_call(self,arg_tuple):
        """
        This function defines what is sent back to whoever called for the fit results
        The error messages should be defined here
        Possibly for later we may want to implement a different class for this, but for now it's here

        It also sends the message based on the sender_function, which is a pre-made function that already comes
        from socketserver.py

        Don't forget to release the lock in the end
        """
        (lock,sender_function,curve_number) = arg_tuple

        doesCurveExist = hasattr(self,self.yaxis_name+"{:d}".format(curve_number))
        if doesCurveExist is False:
            print("Message from Class {:s} function process_fitresults_call: You requested fit results for curve {}, but this curve does not exist.".format(self.__class__.__name__,curve_number))
            sender_function(message_string="nocurve{:02d}".format(curve_number))
            lock.release()
            return None
        doesFitModelExist = hasattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number))
        if doesFitModelExist is False:
            sender_function(message_string="nofitmodel{:02d}".format(curve_number))
            lock.release()
            return None
        doesFitExist = getattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number)).fit_isdone
        if doesFitExist is False:
            sender_function(message_string="nofitdone{:02d}".format(curve_number))
            lock.release()
            return None
        isFitSuccessful = getattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number)).fit_issuccessful
        if isFitSuccessful is False:
            sender_function(message_string="nofitsuccess{:02d}".format(curve_number))
            lock.release()
            return None

        # Here we assemble the message to send and then send it
        # we transmit the resulting paramter values as well as the objective function for a particular fit
        message_fitresults = ""
        for (key,val) in getattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number)).fit_function_paramdict.items():
            message_fitresults += "{:s} : {:.10f}, ".format(key,val)
        message_fitresults += "objectivefunction : {:.10f},".format(getattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number)).fit_result_objectivefunction)
        sender_function(message_string=message_fitresults)
        lock.release()
        return None


    def nofunction(self,verbatim_message):
        print("Function interpreter.message_interpreter could not determine which function to call based on analyzing the transmitted message. Not calling any function. Here is the message that you transmitted (verbatim): {} \n".format(verbatim_message))
    
    def register_available_curves(self):
        self.PlotNumberChoice.clear()
        for idx in range(self.num_datasets):
            if hasattr(self,self.yaxis_name+"{:d}".format(idx)):
                self.PlotNumberChoice.addItem("{:d}".format(idx))        

    def checkAndReturnDataPrefit(self):
        """
        This function checks if the correct curve has been chosen, if the 
        data exists for that curve, and then returns a tuple containing 
        x-vals, y-vals , errorbars (errorbars can be None, the functions 
        downstream should be able to take care of that)
        """
        if self.FitFunctionChoice.currentText() == "None":
            print("Chosen fit function is None. Not doing anything")
            return None
        else:
            try:
                fitCurveNumber = int(self.PlotNumberChoice.currentText())
            except:
                print("Message from Class {:s} function checkAndReturnDataPrefit: fitCurveNumber is undefined. Not doing anything ".format(self.__class__.__name__))
                return None
            if not hasattr(self,self.yaxis_name+"{:d}".format(fitCurveNumber)):
                print("Message from Class {:s}: the curve number that you are trying to fit does not exist. Not doing anything".format(self.__class__.__name__))
                return None
            if len(getattr(self,self.yaxis_name+"{:d}".format(fitCurveNumber))) == 0:
                print("Message from Class {:s}: the curve number that you are trying to fit probably got deleted before. Not doing anything".format(self.__class__.__name__))
                return None

            # if there is no error bar curve, we set it to None, 
            #and then functions downstream will take 
            #care of it
            if hasattr(self,self.err_name+"{:d}".format(fitCurveNumber)):
                if len(getattr(self,self.err_name+"{:d}".format(fitCurveNumber))) == 0:
                    setattr(self,self.err_name+"{:d}".format(fitCurveNumber),None)
            else:
                setattr(self,self.err_name+"{:d}".format(fitCurveNumber),None)

        return (self.x,
                getattr(self,self.yaxis_name+"{:d}".format(fitCurveNumber)),
                getattr(self,self.err_name+"{:d}".format(fitCurveNumber))) 
                # They are not sorted!
        

    def process_MakeFit_button(self):
        fitfunction_name = self.FitFunctionChoice.currentText()
        curve_number = int(self.PlotNumberChoice.currentText())
        
        # If prefit has not been done, we need to generate the data and feed it 
        #into an instance of Fitmodel class before it can be sent to the 
        #fitter
        if not hasattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number)):
            result_check_settings = self.checkAndReturnDataPrefit()
            if result_check_settings is not None:
                setattr(self,
                    self.fitmodel_instance_name+"{:d}".format(curve_number),
                    fm.Fitmodel(fitfunction_name,curve_number,
                        *result_check_settings))
            else:
                print("Message from Class {:s} function process_MakeFit_button: result_check_settings is False, meaning that the data cannot be molded into the correct format to create Fitmodel instance. Check the data".format(self.__class__.__name__))
                return None

        aFitter = GeneralFitter1D(getattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number)))
        aFitter.setupFit(opt_method=self.fitmethod_string)
        # we will now check if the crop data has been set and if so, we will perform the cropping before doing the fit
        if hasattr(self,self.fit_cropbounds_name+"{:d}".format(curve_number)):
            aFitter.cropdata(getattr(self,self.fit_cropbounds_name+"{:d}".format(curve_number)))
        fitres = aFitter.doFit()
        if fitres is True:
            # If the fit result is good, according to the fitter, we want to plot it

            # First we setup the fit curve 
            NUMPOINTS_CURVE = 350
            aXvalsDense = np.linspace(getattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number)).xvals[0],
                    getattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number)).xvals[-1], NUMPOINTS_CURVE)
            fitresults_list = list(getattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number)).fit_function_paramdict.values())
            aYvalsDense = getattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number)).fit_function_base(fitresults_list,aXvalsDense)

            # Now we remove the original line connecting the points but replot
            #the points themselves, and then plot the dashed line for the fit
            #through the same point, in the same color as the points
            measured_data_array = self.convert_to_numpy(self.x,
                        getattr(self,self.yaxis_name+"{:d}".format(curve_number)))
            
            # clear the original plot
            getattr(self,self.plot_line_name+"{:d}".format(curve_number)).clear()
            # set the data plotter to have no pen, so draw no line itself
            setattr(self,self.plot_line_name+"{:d}".format(curve_number),
                    self.graphWidget.plot(symbol="o",
                    pen=pg.mkPen(None),
                    symbolBrush = pg.mkBrush(self.colorpalette[curve_number])))
                    #name=self.legend_label_list[curve_number]))


            # replot the measured data points
            # this setData below is a method of PlotDataItem
            getattr(self,self.plot_line_name+"{:d}".format(curve_number)).setData(*measured_data_array[0:2])

            # if the fit plot aleady exists, clear it, because we don't want
            #multiple plots piling up on each other
            if hasattr(self,self.fitplot_line_name+"{:d}".format(curve_number)):
                getattr(self,self.fitplot_line_name+"{:d}".format(curve_number)).clear()
            
            # finally make a fit plot line and plot the data to it
            setattr(self,self.fitplot_line_name+"{:d}".format(curve_number),
                self.graphWidget.plot(symbol=None,
                    pen=getattr(self,"pen{:d}".format(curve_number)),
                    symbolBrush = pg.mkBrush(None)))
            getattr(self,self.fitplot_line_name+"{:d}".format(curve_number)).setData(aXvalsDense,aYvalsDense)

            # Now let's write the results of the fitting to an output
            #text box below the main plotting window
            self.TextBoxForOutput.setCurrentFont(QtGui.QFont("Helvetica",
                    pointSize=10,
                    weight = QtGui.QFont.Bold))
            self.TextBoxForOutput.append("Curve {:d} fit results:".format(curve_number))
            for (key,val) in getattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number)).fit_function_paramdict.items():
                self.TextBoxForOutput.setCurrentFont(QtGui.QFont("Helvetica",
                    pointSize=10,
                    weight=QtGui.QFont.Normal))
                self.TextBoxForOutput.append(key+" : "+"{:.06f}".format(val))
        #this else condition will be used if the fit result is not a success
        else:
            print("Message from Class {:s} function process_MakeFit_button: Fit is not successful, not plotting anything".format(self.__class__.__name__))
        if self.prefitDialogWindow:
            self.prefitDialogWindow.close()
        #TODELETE
        print("Fit result dictionary output: ",getattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number)).fit_function_paramdict)

    # TODO Somehow prefit seems to not accept it when the initial parameter is set to 0. Check that out
    def process_Prefit_button(self):
        result_check_settings = self.checkAndReturnDataPrefit()
        if result_check_settings:
            # get the current name of the fit function and the curve number to fit
            #remember that FitFunctionChoice and PlotNumberChoice are the GUI 
            #QComboBox widgets
            fitfunction_name = self.FitFunctionChoice.currentText()
            curve_number = int(self.PlotNumberChoice.currentText())

            # if the fitmodel_instance already exists, check if the required 
            #fit function is the same as is in the existing fitmodel_instance.
            #If not, delete fitmodel_instance and start again
            #if fitmodel_instance does not exist, then create it
            if hasattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number)):
                if getattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number)).fitfunction_name_string != fitfunction_name:
                    print("Message from Class {:s} function process_Prefit_button: you changed the fit function for the curve which you already tried to process in prefit. Erasing all previous prefit parameters".format(self.__class__.__name__))
                    delattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number))
                    setattr(self,
                        self.fitmodel_instance_name+"{:d}".format(curve_number),
                        fm.Fitmodel(fitfunction_name,curve_number,
                            *result_check_settings))
                else:
                    pass
            else:
                setattr(self,
                        self.fitmodel_instance_name+"{:d}".format(curve_number),
                    fm.Fitmodel(fitfunction_name,
                        curve_number,*result_check_settings))
        else:
            print("Message from function process_Prefit_button: checkAndReturnDataPrefit function failed, check out its error messages and input data")
            return None
       
        # Now we create the actual prefit dialog window (popup) 
        # If prefitDialogWindow does not exist, we have to create it
        if self.prefitDialogWindow is None: 
            self.prefitDialogWindow = PrefitterDialog(getattr(self,
                self.fitmodel_instance_name+"{:d}".format(curve_number)))
        #otherwise we close and open it again with the correct prefitter
        else:
            self.prefitDialogWindow.close()
            self.prefitDialogWindow = PrefitterDialog(getattr(self,
                self.fitmodel_instance_name+"{:d}".format(curve_number)))
        
        self.prefitDialogWindow.show()

    def process_Crop_button(self):
        try:
            upperlim = float(self.CropUpperLimit.text())
        except ValueError:
            upperlim = None
            print("Message from Class {} function process_Crop_button: upper crop limit is invalid, setting to None".format(self.__class__.__name__))

        try:
            lowerlim = float(self.CropLowerLimit.text())
        except ValueError:
            lowerlim = None
            print("Message from Class {} function process_Crop_button: lower crop limit is invalid, setting to None".format(self.__class__.__name__))

        self.set_crop_tuple((lowerlim,upperlim))

    def showdata(self,data):
        print(data)

    def convert_to_numpy(self,*args,doSort=True):
        """
        This is a helper function which simply takes a list of arguments, 
        where the inner lists are supposed to be convertible to numpy arrays, 
        and converts them to numpy arrays, returning a list of numpy arrays 
        """
        if doSort: 
            arr0 = np.array(args[0])
            arr0_arguments = np.argsort(arr0)
            result = [np.array(arg,dtype=np.float)[arr0_arguments] for arg in args]
            return result
        else:
            result = [np.array(arg) for arg in args]
            return result


    def _create_plotline(self,curvenumber: int) -> bool:
        """
        Just a helper function in order to create the plot line if it doesn't already
        exist
        This is for adding new curves to the plot. Do not call on existing curves!
        """
        # First check if the legend label already exists, and if not, add an automatic label
        # to just give the curve number
        if "curve{:d}".format(curvenumber) not in self.legend_label_dict:
            self.legend_label_dict["curve{:d}".format(curvenumber)] = "c{:d}".format(curvenumber)

        # Now set all the attributes to make sure that the corresponding curve exists
        setattr(self, self.xaxis_name + "{:d}".format(curvenumber),[])
        setattr(self, self.yaxis_name + "{:d}".format(curvenumber),[])
        setattr(self, self.err_name + "{:d}".format(curvenumber),[])
        setattr(self, self.pen_name + "{:d}".format(curvenumber), pg.mkPen(color=self.colorpalette[curvenumber],
                                                          style=QtCore.Qt.DashLine))

        setattr(self, self.errorbar_pen_name + "{:d}".format(curvenumber),
                 pg.mkPen(color=self.colorpalette[curvenumber],
                          style=QtCore.Qt.SolidLine))
        setattr(self, self.plot_line_name + "{:d}".format(curvenumber),
                 self.graphWidget.plot(symbol="o", name=self.legend_label_dict["curve{:d}".format(curvenumber)],
                                       pen=getattr(self, self.pen_name + "{:d}".format(curvenumber)),
                                       symbolBrush=pg.mkBrush(self.colorpalette[curvenumber])))
        return True


    # This function is for real-time plotting of data points, 
    #just as they come in through TCP/IP
    # this is called directly from interpreter basically!
    #def generate_plot_pointbypoint(self,datapoint): # this is the old name for the plotting function
    def plot_single_datapoint(self,plot_single_datapoint_arg: dict) -> bool:
        """
        OLD: data points are supposed to be sent as tuples in the format (x_val,[y1_val,y2_val,...],[y1_err,y2_err,...]). If the length of the tuple is 3, we have error bars, if the length of the tuple is 2, we do not have error bars
        """

        # =============== Data format check ================================
        # We first have to check if the data format for this data point dictionary is correct
        # if it is not, we don't plot anything
        possible_datapoint_keys = ["curveNumber", "xval", "yval", "yerr", "xerr"]
        critical_keys = ["curveNumber", "xval", "yval"]
        if isinstance(plot_single_datapoint_arg,dict):
            # First check that all keys supplied are legal
            if not all([key in possible_datapoint_keys for key in plot_single_datapoint_arg.keys()]):
                print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "plot_single_datapoint"))
                print("Some of the keys you supplied to dataPoint are not in the legal key list. Here is the legal key list: {}. Not doing anything".format(possible_datapoint_keys))
                return False
            # Now check that we have the absolutely necessary keys for plotting the point
            if not all([crit_key in plot_single_datapoint_arg for crit_key in critical_keys]):
                print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "plot_single_datapoint"))
                print("You must provide at least all of these keys {} to plot a point, but you didn't. Not plotting anything".format(
                        critical_keys))
                return False
            # Now check that the curve number is an integer
            if not isinstance(plot_single_datapoint_arg["curveNumber"],int):
                print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "plot_single_datapoint"))
                print("You put a curve number that is not an integer. This is not allowed")
                return False
            # Now check that the xval is either an intereg or a float
            if not isinstance(plot_single_datapoint_arg["xval"],(int,float)):
                print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "plot_single_datapoint"))
                print("Your xval is not numeric. This is not allowed")
                return False
            # Now check that the yval is either an integer or a float
            if not isinstance(plot_single_datapoint_arg["yval"],(int,float)):
                print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "plot_single_datapoint"))
                print("Your yval is not numeric. This is not allowed")
                return False
            # Now check if xerr, if it is given, is an integer or a float
            if "xerr" in plot_single_datapoint_arg:
                if not isinstance(plot_single_datapoint_arg["xerr"],(int,float)):
                    print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "plot_single_datapoint"))
                    print("Your xerr is not numeric. This is not allowed")
                    return False
                is_this_xerr_given = True
            else:
                is_this_xerr_given = False
            # Now check if yerr, if it is given, is an integer or a float
            if "yerr" in plot_single_datapoint_arg:
                if not isinstance(plot_single_datapoint_arg["yerr"],(int,float)):
                    print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "plot_single_datapoint"))
                    print("Your yerr is not numeric. This is not allowed")
                    return False
                is_this_yerr_given = True
            else:
                is_this_yerr_given = False

            # ======= Done with syntax checking for the message =============
            # If we made it to here, it means that the message into plot_single_datapoint is correct

            this_curvenumber = plot_single_datapoint_arg["curveNumber"]
            # This is the case when the plot line already exists
            if not hasattr(self,self.plot_line_name+"{:d}".format(this_curvenumber)):
                self._create_plotline(this_curvenumber)

            getattr(self, self.xaxis_name + "{:d}".format(this_curvenumber)).append(plot_single_datapoint_arg["xval"])
            getattr(self, self.yaxis_name + "{:d}".format(this_curvenumber)).append(plot_single_datapoint_arg["yval"])
            # This is the case when the points come with error bars
            if is_this_yerr_given is True:
                getattr(self, self.err_name + "{:d}".format(this_curvenumber)).append(
                    plot_single_datapoint_arg["yerr"])
                arrays_toplot = self.convert_to_numpy(getattr(self,self.xaxis_name + "{:d}".format(this_curvenumber)),
                                                      getattr(self,self.yaxis_name + "{:d}".format(this_curvenumber)),
                                                      getattr(self,self.err_name + "{:d}".format(this_curvenumber)))
                setattr(self, self.errorbar_item_name + "{:d}".format(this_curvenumber),
                        pg.ErrorBarItem(x=arrays_toplot[0], y=arrays_toplot[1],
                                        top=arrays_toplot[2], bottom=arrays_toplot[2],
                                        pen=getattr(self, self.errorbar_pen_name + "{:d}".format(this_curvenumber))))
                self.graphWidget.addItem(getattr(self, self.errorbar_item_name + "{:d}".format(this_curvenumber)))
                getattr(self, self.plot_line_name + "{:d}".format(this_curvenumber)).setData(*arrays_toplot[0:2])
            else:
                arrays_toplot = self.convert_to_numpy(
                    getattr(self, self.xaxis_name + "{:d}".format(this_curvenumber)),
                    getattr(self, self.yaxis_name + "{:d}".format(this_curvenumber)))
                getattr(self, self.plot_line_name + "{:d}".format(this_curvenumber)).setData(*arrays_toplot[0:2])
            return True

        else:
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "plot_single_datapoint"))
            print("You supplied something other than a dictionary as the function argument. Not doing anything")
            return False


    def clear_plot(self,dummyargument: str):
        """
        This only clear the visual from the plot, it doesn't clear the saved data
        """
        self.graphWidget.clear()
        self.arePlotsCleared = True
        if hasattr(self, self.legend_item_name):
            getattr(self, self.legend_item_name).clear()

    def clear_data(self,clear_data_arg: int) -> bool:
        if clear_data_arg == "all":
            self.x = []
            for idx in range(MAX_CURVES):
                for attr_name in self.all_instance_attribute_names:
                    if hasattr(self,attr_name+"{:d}".format(idx)):
                        delattr(self,attr_name+"{:d}".format(idx))
                    else:
                        pass
            self.clear_plot("")
            self.num_datasets = 0
            self.PlotNumberChoice.clear()
            self.legend_label_list = []
            if hasattr(self, self.legend_item_name):
                getattr(self, self.legend_item_name).clear()
            return True
        # TODO maybe implement the idea of deleting curves one by one
        elif isinstance(clear_data_arg,int):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__,"clear_data"))
            print("This argument type has not been implemented yet. Doing nothing")
            return False # for now, so that it doesn't fail
            # The code below is unreachable, but that's OK, it's not ready yet
        else:
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__,"clear_data"))
            print("Your argument to clear_data is: {} . This is not allowed. Not doing anything".format(clear_data_arg))
            return False

    def set_axis_labels(self,axis_labels_arg: List[str]) -> bool:
        if len(axis_labels_arg) != 2:
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__,"set_axis_labels"))
            print("You supplied something other than 2 arguments to this function. This is not allowed, you must supply a list of exactly 2 strings, for x-label and y-label. Not doing anything")
            return False
        if all([isinstance(entry,str) for entry in axis_labels_arg]):
            self.graphWidget.setLabels(bottom=axis_labels_arg[0],left=axis_labels_arg[1])
            return True
        else:
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__,"set_axis_labels"))
            print("You supplied two arguments, but at least one is not of type str. This is not allowed. Not doing anything.")
            return False

    def set_plot_title(self,plot_title_arg: str) -> bool:
        if isinstance(plot_title_arg,str):
            self.graphWidget.setTitle(title=plot_title_arg)
            return True
        else:
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__,"set_plot_title"))
            print("You supplied something other than 1 argument into this function, or the argument is not a string. Not doing anything")
            return False
    
    def set_plot_legend(self,set_plot_legend_arg: dict) -> bool:
        if isinstance(set_plot_legend_arg,dict):
            # the case that our plot legend parameter is a dictionary, as expected
            if all([isinstance(key,str) for key in set_plot_legend_arg]):
                # if all keys and values are strings, as expected, we save them
                self.legend_label_dict = set_plot_legend_arg
                self.legend_label_list = list(set_plot_legend_arg.values())
            else:
                # else we throw away everything that is not strings
                for key in set_plot_legend_arg:
                    if (not isinstance(key,str)) or (not isinstance(set_plot_legend_arg[key],str)):
                        print("Message from Class {:s} function {:s}".format(self.__class__.__name__,"set_plot_legend"))
                        print("You inserted a key-value pair where one of the elements is not a string: {} : {}. This is not allowed, deleting this key-value pair".format(key,set_plot_legend_arg[key]))
                        set_plot_legend_arg.pop(key)
                # and once we deleted all the non-string inputs, we can save the dictionary
                self.legend_label_dict = set_plot_legend_arg
                self.legend_label_list = list(set_plot_legend_arg.values())
            return True
        else:
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "set_plot_legend"))
            print("The parameter that you gave into set_plot_legend is not a dictionary. This is not allowed, erasing legends")
            self.legend_label_dict = {}
            self.legend_label_list = []
            return False

    def set_fit_function(self,fitfunctionname):
        if isinstance(fitfunctionname,str):
            fitfunction_index = self.FitFunctionChoice.findText(fitfunctionname)
            if fitfunction_index > -1:
                self.FitFunctionChoice.setCurrentIndex(fitfunction_index)
            else:
                print("Message from Class {:s} function set_fit_function: fit function name {} does not exist. Check also if the curves are registered".format(self.__class__.__name__,fitfunctionname))
    def set_curve_number(self,curvenumber_str):
        # First, we check if the curve number is sensible
        try:
            curve_num_int = int(curvenumber_str)
            if curve_num_int < 0:
                print("Message from Class {:s} function set_curve_number: You are trying to set a negative curve number. This is impossible".format(self.__class__.__name__))
                return None
        except:
            print("Message from Class {:s} function set_curve_number: You are trying to set a non-integer curve number. This is impossible".format(self.__class__.__name__))
            return None
        # We have to register the available curves, so that 
        #we can choose
        self.register_available_curves()
        curvenumber_index = self.PlotNumberChoice.findText(curvenumber_str)
        if curvenumber_index > -1:
            self.PlotNumberChoice.setCurrentIndex(curvenumber_index)
        else:
            print("Message from Class {:s} function set_curve_number: curve number {} does not exist. Check also if the curves are registered".format(self.__class__.__name__,curvenumber_str))
    
    def set_starting_parameters(self,parameterdictionary):
        # we start with doing process_Prefit_button, because it's exactly the same 
        #function as there, we are supposed to format the data into the correct 
        #shape, and initialize the prefit dictinoary in order to be 
        #able to fill it with the suggested starting values
        self.process_Prefit_button()
        current_curve_number_string = self.PlotNumberChoice.currentText()
        for key in parameterdictionary:
            if key in getattr(self,self.fitmodel_instance_name+current_curve_number_string).fit_function_paramdict_prefit:
                getattr(self,self.fitmodel_instance_name+current_curve_number_string).fit_function_paramdict_prefit[key] = parameterdictionary[key]
            else:
                print("Message from Class {:s} function set_starting_parameters : you input key {} into the parameter dictionary, and the selected fit model is {}. Such a parameter for the selected fit model does not exist. Not setting this parameter".format(self.__class__.__name__,key,self.FitFunctionChoice.currentText()))
    def set_crop_tuple(self,croptuple): # this sets the crop tuple for cropping the x-axis before data fitting
        current_curve_number_string = self.PlotNumberChoice.currentText()
        setattr(self,self.fit_cropbounds_name+current_curve_number_string,croptuple)

    def do_fit(self,emptystring):
       self.process_MakeFit_button() 

    def buttonHandler(self,textmessage="blahblahblah"): # we can get the arguments in using functools.partial, or better take no arguments
        print(textmessage)

    def closeEvent(self,event):
        if self.prefitDialogWindow:
            self.prefitDialogWindow.close()

def runPlotter(sysargs):

    HOST = "127.0.0.1"
    #HOST = "134.93.88.156"
    
    # this is the server for one-way communication, no responses
    PORT = 5757
    myServer = TCPIPserver(HOST,PORT)
    myServer.reportedLengthMessage = True
    
    # We want to call this server for two-way communication to send back
    #fit results
    PORT_TWOWAY = PORT + 1
    myServerTwoway = TCPIPserver(HOST,PORT_TWOWAY)
    myServerTwoway.reportedLengthMessage = True


    app = QtWidgets.QApplication(sysargs)
    w = MainWindow(myServer,myServerTwoway)
    #w.show()
    app.exec_()
    if w.prefitDialogWindow:
        w.prefitDialogWindow.close()
    print("done with the plotter")


if __name__ == "__main__":
    runPlotter(sys.argv)
    # TEST
