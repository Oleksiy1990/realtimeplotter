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
from fitmodelclass import Fitmodel
from mathfunctions import fitmodels
import helperfunctions
from typing import Optional, Tuple, List, Any, Union
import socket

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
    #finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(tuple)
    request_to_main = QtCore.pyqtSignal(object)
    set_client_communication_socket = QtCore.pyqtSignal(object) # maybe the argument should be socket.socket, not sure now
    newdata = QtCore.pyqtSignal(str) # This is what apparently the spawned socket emits after parsing the data

class TCP_IP_Worker(QtCore.QRunnable):
    """
    This is to process TCP/IP requests in Threads
    
    Note that the only thing that this really does is to get a listener function 
    as an argument, it also makes a WorkerSignals() instance, and then it defines a run()
    method, makes it a slot, and when it's called, it passes the WorkerSignals instance to the listener function

    Worker thread

        Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

        :param callback: The function callback to run on this worker thread. Supplied args and
                         kwargs will be passed through to the runner.
        :type callback: function
        :param args: Arguments to pass to the callback function
        :param kwargs: Keywords to pass to the callback function

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

class MainWindow(QtGui.QMainWindow):

    # These are class variables, or effetively constants for our purposes
    DEFINED_FITFUNCTIONS = ["sinewave","damped_sinewave","gaussian","curvepeak","linearfit","parabolicfit","resonancetrackingzero"]
    MAX_NUM_CURVES = 50 # This is a large upper limit on the max number of curves that
                        # can be plotted at the same time
    NUMPOINTS_CURVE_DENSE = 350

    def __init__(self, aTCPIPserver):

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
        # The numerical data inputs
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

        self.all_instance_attribute_config_names = []

        self.legend_label_list = [] # processed in self._create_plotline
        self.legend_label_dict = {}

        #self.myJSONread = JSONread()

        # This is the number of datasets in the current state of the class instance
        self.num_datasets = 0
        self.arePlotsCleared = True
        self.prefitDialogWindow = None

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
        self.RegisterCurvesButton.clicked.connect(self._register_available_curves)
        self.MakeFitButton.clicked.connect(self.process_makefit_button)
        self.PrefitButton.clicked.connect(self.process_Prefit_button)
        
        self.FitFunctionChoice = QtGui.QComboBox()
        self.PlotNumberChoice = QtGui.QComboBox()
        self.FitFunctionChoice.addItems(self.DEFINED_FITFUNCTIONS)
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
        #myTCP_IP_Worker_Twoway = TCP_IP_Worker(aTCPIPServerTwoway.listener_function_Twoway)
        myTCP_IP_Worker.signals.newdata.connect(self.interpret_message)
        myTCP_IP_Worker.signals.set_client_communication_socket.connect(self._register_client_communication_socket)
        #myTCP_IP_Worker_Twoway.signals.request_to_main.connect(self.process_fitresults_call)
        self.threadpool.start(myTCP_IP_Worker)
        #self.threadpool.start(myTCP_IP_Worker_Twoway)
        self.client_communication_socket = None # This will be the socket to use for sending data to the client

    ###### End of __init__()
    def _register_client_communication_socket(self, socket_arg: socket.socket) -> bool:
        if not isinstance(socket_arg,(socket.socket,type(None))):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "_register_client_communication_socket"))
            print(
                "The argument you put into this function is not type socket.socket or None. Not doing anything")
            return False
        self.client_communication_socket = socket_arg
        return True

    def interpret_message(self,message: str) -> None:
        """
        Message is supposed to be a string. 
        The result is a list of tuples. Each tuple has the form 
        ("function name",argument)
        """

        # This should not be needed anymore, because we do not emit these messages anymore
        #if (message == "Done") or (message == ""):
        #    return None # This is because somehow socketserver.py sends these things.
        # TODO: improve the socket server class

        myJSONread = JSONread()
        interpretation_result = myJSONread.parse_JSON_message(message)
        # the line above produces a list of tuples form the JSON-RPC message

        # IMPORTANT! Be careful with this because this is where the functions from the received
        #JSON-RPC message get called, but they are not explicitly written with their names
        # we use metaprogramming here all over the place with setattr and getattr functions

        # the first element of the tuple is always the string name of the function to call
        # the second element is always the parameter to feed into the function
        for res in interpretation_result:
            function_to_call = getattr(self,res[0],self.nofunction)
            type(function_to_call)
            function_to_call(res[1])
        self.message_processed = True


    def nofunction(self,verbatim_message: str) -> None:
        print("Function interpreter.message_interpreter could not determine which function to call based on analyzing the transmitted message. Not calling any function. Here is the message that you transmitted (verbatim): {} \n".format(verbatim_message))

    # TODO: Get rid of this function and button correctly. They are registered immediately as they come in.
    def _register_available_curves(self) -> None:
        self.PlotNumberChoice.clear()
        for idx in range(self.MAX_NUM_CURVES):
            if hasattr(self,self.plot_line_name+"{:d}".format(idx)):
                self.PlotNumberChoice.addItem("{:d}".format(idx))        

    def process_makefit_button(self) -> bool:

        # If we are going to do the fit, we should close the prefit dialog window no matter what
        if self.prefitDialogWindow:
            self.prefitDialogWindow.close()

        current_curve_number = int(self.PlotNumberChoice.currentText())
        if not hasattr(self,self.fitmodel_instance_name+"{:d}".format(current_curve_number)):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "process_makefit_button"))
            print("You put a curve number that is not an integer. This is not allowed")
            return False
        # Now comes the fitting part
        # 1) Create a fitter instance
        currentFitter = GeneralFitter1D(getattr(self,self.fitmodel_instance_name+"{:d}".format(current_curve_number)))
        # 2) setup fit
        result_setupfit = currentFitter.setup_fit()

        if result_setupfit is True:
            # 3) perform the fit
            result_dofit = currentFitter.do_fit()
            if getattr(self,self.fitmodel_instance_name+"{:d}".format(current_curve_number)).result_objectivefunction == -1:
                result_regularplot = False
            else:
                result_regularplot = True
        else:
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "process_makefit_button"))
            print("setup_fit() function from the fitter class returned False. Fitting impossible. Not doing anything \n")
            return False

        if (result_dofit is True) and (result_regularplot is True):
            # 4) If the fit result is good, according to the fitter message, we want to plot it
            if getattr(self,self.fitmodel_instance_name+"{:d}".format(current_curve_number)).is_fit_successful is True:
                aXvalsDense = np.linspace(getattr(self,
                        self.fitmodel_instance_name+"{:d}".format(current_curve_number)).xvals[0],
                        getattr(self,self.fitmodel_instance_name+"{:d}".format(current_curve_number)).xvals[-1],
                        self.NUMPOINTS_CURVE_DENSE)
                fitresults_list = list(getattr(self,
                        self.fitmodel_instance_name+"{:d}".format(current_curve_number)).result_paramdict.values())
                fitfunction_callable = getattr(fitmodels,
                        getattr(self,self.fitmodel_instance_name+"{:d}".format(current_curve_number)).fitfunction_name_string+"_base")
                aYvalsDense = fitfunction_callable(fitresults_list,aXvalsDense)
                # Now we remove the original line connecting the points but replot
                #the points themselves, and then plot the dashed line for the fit
                #through the same point, in the same color as the points
                measured_data_array = self.convert_to_numpy(
                        getattr(self,self.xaxis_name+"{:d}".format(current_curve_number)),
                            getattr(self,self.yaxis_name+"{:d}".format(current_curve_number)))

                # clear the original plot
                getattr(self,self.plot_line_name+"{:d}".format(current_curve_number)).clear()
                # and make sure to clear the legend otherwise it will be repeated with every fit
                getattr(self,self.legend_item_name).removeItem(getattr(self,self.plot_line_name+"{:d}".format(current_curve_number)))

                # set the data plotter to have no pen, so draw no line itself
                setattr(self,self.plot_line_name+"{:d}".format(current_curve_number),
                        self.graphWidget.plot(symbol="o",
                        pen=pg.mkPen(None),
                        name=self.legend_label_dict["curve{:d}".format(current_curve_number)],
                        symbolBrush = pg.mkBrush(self.colorpalette[current_curve_number])))

                # replot the measured data points
                # this setData below is a method of PlotDataItem
                getattr(self,self.plot_line_name+"{:d}".format(current_curve_number)).setData(*measured_data_array[0:2])

                # if the fit plot aleady exists, clear it, because we don't want
                #multiple plots piling up on each other
                if hasattr(self,self.fitplot_line_name+"{:d}".format(current_curve_number)):
                    getattr(self,self.fitplot_line_name+"{:d}".format(current_curve_number)).clear()

                # finally make a fit plot line and plot the data to it
                setattr(self,self.fitplot_line_name+"{:d}".format(current_curve_number),
                    self.graphWidget.plot(symbol=None,
                        pen=getattr(self,"pen{:d}".format(current_curve_number)),
                        symbolBrush = pg.mkBrush(None)))
                getattr(self,self.fitplot_line_name+"{:d}".format(current_curve_number)).setData(aXvalsDense,aYvalsDense)

                #============= Ok by here we should be done with the actual plotting of the fit

                # Now let's write the results of the fitting to an output
                #text box below the main plotting window
                self.TextBoxForOutput.setCurrentFont(QtGui.QFont("Helvetica",
                        pointSize=10,
                        weight = QtGui.QFont.Bold))
                self.TextBoxForOutput.append("Curve {:d} {} fit results:".format(current_curve_number,
                                            self.legend_label_dict["curve{:d}".format(current_curve_number)]))
                # Write a warning message if the error bars were wrong (so at least one was 0)
                if getattr(self,self.fitmodel_instance_name+"{:d}".format(current_curve_number)).are_errorbars_correct is False:
                    self.TextBoxForOutput.append("WARNING! Curve {:d} {}: you supplied wrong error bars! One of the error bars was 0. Error bars were ignored in the fit".format(current_curve_number,
                        self.legend_label_dict["curve{:d}".format(current_curve_number)]))
                for (key,val) in getattr(self,self.fitmodel_instance_name+"{:d}".format(current_curve_number)).result_paramdict.items():
                    self.TextBoxForOutput.setCurrentFont(QtGui.QFont("Helvetica",
                        pointSize=10,
                        weight=QtGui.QFont.Normal))
                    self.TextBoxForOutput.append(key+" : "+"{:.06f}".format(val))
                self.TextBoxForOutput.append("Objective function result" + " : " + \
                    "{:.06f}".format(getattr(self,self.fitmodel_instance_name+"{:d}".format(current_curve_number)).result_objectivefunction))
                return True
            else:
                self.TextBoxForOutput.setCurrentFont(QtGui.QFont("Helvetica",
                                                                 pointSize=10,
                                                                 weight=QtGui.QFont.Bold))
                self.TextBoxForOutput.append(
                    "Curve {:d} {} : Fit failed".format(current_curve_number,
                                    self.legend_label_dict["curve{:d}".format(current_curve_number)]))
                return True
        elif (result_dofit is True) and (result_regularplot is False):
            # Now let's write the results of the fitting to an output
            #text box below the main plotting window
            self.TextBoxForOutput.setCurrentFont(QtGui.QFont("Helvetica",
                    pointSize=10,
                    weight = QtGui.QFont.Bold))
            self.TextBoxForOutput.append("Curve {:d} {} fit results:".format(current_curve_number,
                                        self.legend_label_dict["curve{:d}".format(current_curve_number)]))
            for (key,val) in getattr(self,self.fitmodel_instance_name+"{:d}".format(current_curve_number)).result_paramdict.items():
                self.TextBoxForOutput.setCurrentFont(QtGui.QFont("Helvetica",
                    pointSize=10,
                    weight=QtGui.QFont.Normal))
                self.TextBoxForOutput.append(key+" : "+"{}".format(val))
            return True
        #this else condition will be used if the fit result is not a success
        else:
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "process_makefit_button"))
            print("do_fit function failed in the fitter. Check other error messages")
            return False

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
                        Fitmodel(fitfunction_name,curve_number,
                            *result_check_settings))
                else:
                    pass
            else:
                setattr(self,
                        self.fitmodel_instance_name+"{:d}".format(curve_number),
                    Fitmodel(fitfunction_name,
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

        Important! This adds the legend to the plot as well
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
        # Now finally add the curve to the list of available curves
        self.PlotNumberChoice.addItem("{:d}".format(curvenumber))
        return True
        # TODO: Make sure to delete PlotNumberChoice entry when the clear command is issued

    def _clear_curve(self,curvenumber: int) -> bool:
        # First we remove everything from the plot for this curve
        if hasattr(self, self.errorbar_item_name + "{:d}".format(curvenumber)):
            #TODELETE
            print("in GUI.py _clear_curve trying to remove errorbar_item")
            #self.graphWidget.removeItem(getattr(self, self.errorbar_item_name + "{:d}".format(curvenumber)))
            getattr(self, self.errorbar_item_name + "{:d}".format(curvenumber)).setData(pen=pg.mkPen(None))

        if hasattr(self,self.plot_line_name+"{:d}".format(curvenumber)):
            #getattr(self,self.plot_line_name+"{:d}".format(curvenumber)).clear()
            self.graphWidget.removeItem(getattr(self,self.plot_line_name+"{:d}".format(curvenumber)))
        if hasattr(self, self.fitplot_line_name + "{:d}".format(curvenumber)):
            #getattr(self, self.fitplot_line_name + "{:d}".format(curvenumber)).clear()
            self.graphWidget.removeItem(getattr(self, self.fitplot_line_name + "{:d}".format(curvenumber)))
        if hasattr(self, self.errorbar_item_name + "{:d}".format(curvenumber)):
            #TODELETE
            print("in GUI.py _clear_curve trying to remove errorbar_item")
            #self.graphWidget.removeItem(getattr(self, self.errorbar_item_name + "{:d}".format(curvenumber)))
            getattr(self, self.errorbar_item_name + "{:d}".format(curvenumber)).setData(bottom=0,
                                                                                        top=0)

        for entry in self.all_instance_attribute_names:
            if hasattr(self,entry+"{:d}".format(curvenumber)):
                delattr(self,entry+"{:d}".format(curvenumber))
        return True


    # This function is for real-time plotting of data points, 
    #just as they come in through TCP/IP
    # this is called directly from interpreter basically!
    #def generate_plot_pointbypoint(self,datapoint): # this is the old name for the plotting function
    def plot_single_datapoint(self,plot_single_datapoint_arg: dict) -> bool:
        """
        Plots a data point as it comes in from the client
        
        This function is for real-time plotting of data points, 
        just as they come in through TCP/IP.
        This is called directly from the signal-slot mechanism, and the function in 
        JSONinterpreter.py that calls it is __parse_addData_message()
                
        Parameters
        ----------
        plot_single_datapoint_arg: dict
            Required key-value pairs for each plot_single_datapoint_arg: 
                "curvenumber":int (integer defining to which curve we will add the incoming point) 
                "xval":float,int (the x-coordinate of the incoming point)
                "yval":float,int (the y-coordinate of the incoming point)
            Optional key-value pairs for each plot_single_datapoint_arg: 
                "xerr":float,int (the horizontal error bar for the incoming point)
                "yerr":float,int (the vertical error bar for the incoming point)
            
        Returns
        -------
        bool
            True if the function finished correctly, False, if there was an error
            Check error messages for explanations of errors
        
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
            # Now check that there are not more curves trying to be registered than the max allowed number
            if plot_single_datapoint_arg["curveNumber"] >= self.MAX_NUM_CURVES:
                print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "plot_single_datapoint"))
                print("You put a curve number which is greater than MAX_NUM_CURVES, which is now set to {:d}. This is not allowed".format(self.MAX_NUM_CURVES))
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

    def clear_data(self,clear_data_arg: Union[int,str]) -> bool:
        """
        Remove a particular unit of data from memory
        
        Clears whatever curve is asked, meaning the original data, fits. It also runs _register_available_curves
        at the end so as to make sure that the remaining curves are correctly registered and available for 
        further processing 
        
        Parameters
        ----------
        clear_data_arg: int, str
            If str, it must be "all", which will clear all curves
            If int, it's the curve number that one wants to clear
            
        Returns
        -------
        bool
            True if the function finished correctly, False, if there was an error
            Check error messages for explanations of errors
        
        """
        if not isinstance(clear_data_arg, (int,str)):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "clear_data"))
            print("You supplied something other than an integer or string as the function argument. Not doing anything \n")
            return False

        if clear_data_arg == "all":
            for idx in range(self.MAX_NUM_CURVES):
                self._clear_curve(idx)
            self.clear_plot("") # TODO! Make sure that this works correctly for clearing individual curves
            getattr(self, self.legend_item_name).clear()
            self.PlotNumberChoice.clear() # Clear all choices because there are no curves left at this point
            return True

        if not isinstance(clear_data_arg,int):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "clear_data"))
            print(
                "You supplied something other than all or integer into clear_data. This command cannot be performed \n")
            return False

        self._clear_curve(clear_data_arg)
        self._register_available_curves() # This will clear out the plot number choice box, and then register again what's left
        return True

    def clear_config(self,clear_config_arg: str) -> bool:
        """
        Removes plot configurations
        
        Parameters
        ----------
        clear_config_arg: str
            If str is "all", it will clear the axis labels and the plot title
            
            In the future, the goal is to implement clearing axis labels and title separately
            
        Returns
        -------
        bool
            True if the function finished correctly, False, if there was an error
            Check error messages for explanations of errors
        
        """
        if not isinstance(clear_config_arg, str):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "clear_config"))
            print("You supplied something other than a string as the function argument. Not doing anything \n")
            return False
        if clear_config_arg == "all":
            self.graphWidget.setLabel('bottom',text="")
            self.graphWidget.setLabel('left',text="")
            self.graphWidget.setTitle(title="")
            return True
        else:
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "clear_config"))
            print("You supplied the string argument that is different from all. This is not yet implemented. Not doing anything \n")
            return False
            
    def set_axis_labels(self,axis_labels_arg: List[str]) -> bool:
        """
        Puts x-axis label (below) and y-axis label (left)
        
        Parameters
        ----------
        axis_labels_arg: list of two strings
            The first string is the a-axis label, the second string is the y-axis label
            
        Returns
        -------
        bool
            True if the function finished correctly, False, if there was an error
            Check error messages for explanations of errors
        
        """
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
        """
        Sets the plot title (above)
        
        Parameters
        ----------
        plot_title_arg: str
            
        Returns
        -------
        bool
            True if the function finished correctly, False, if there was an error
            Check error messages for explanations of errors
        
        """
        if isinstance(plot_title_arg,str):
            self.graphWidget.setTitle(title=plot_title_arg)
            return True
        else:
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__,"set_plot_title"))
            print("You supplied something other than 1 argument into this function, or the argument is not a string. Not doing anything")
            return False
    
    def set_plot_legend(self,set_plot_legend_arg: dict) -> bool:
        """
        Sets up the legend with the labels that the curves will have when they are plotted
        
        Parameters
        ----------
        plot_legend_arg: dict
            For each entry: 
            key: "curve0" or "curve1", or etc. (so the word "curve" with the number 
                the curve given as a string)
            value: str which represents whatever has to be put on the legend for this curve 
                This can be anything, as long as it is a string
        Returns
        -------
        bool
            True if the function finished correctly, False, if there was an error
            Check error messages for explanations of errors
        
        """
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

    def set_fit_function(self,fit_function_name: str) -> bool:
        """
        Sets the fit function to use in case fitting is called, based on its string name. 
        The fit function must be defined in fitmodels.py
                
        Parameters
        ----------
        fit_function_name: str
            For example it could be "gaussian" or "sinewave", etc. 
            
        Returns
        -------
        bool
            True if the function finished correctly, False, if there was an error
            Check error messages for explanations of errors
        
        """
        if isinstance(fit_function_name,str):
            if fit_function_name in self.DEFINED_FITFUNCTIONS:
                self.FitFunctionChoice.setCurrentText(fit_function_name)
                #current_curvenumber = int(self.PlotNumberChoice.currentText())
                #current_fitmodel = getattr(self,self.fitmodel_instance_name+"{:d}".format(current_curvenumber))
                #current_fitmodel.fitfunction_name = fit_function_name
                return True
            else:
                print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "set_fit_function"))
                print("Fit function name {} is not defined \n".format(fit_function_name))
                return False
        else: #else the fit function name is not a string, this doesn't work
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "set_fit_function"))
            print("You set a fit function name which is not a string. This is not allowed \n")
            return False

    def set_curve_number(self,curvenumber_arg: int) -> bool:
        """
        Sets the curve number to be used in this particular iteration of doFit. 
        This will then determine the curve which is fitted, and consequently for which 
        the fit parameters will be given, also possibly cropping, etc. 
                
        Parameters
        ----------
        curvenumber_arg: int
            
        Returns
        -------
        bool
            True if the function finished correctly, False, if there was an error
            Check error messages for explanations of errors
        
        """
        
        # The goal of this function is to check if the corresponding
        # curve number exists, and if it does, then it will 
        # make an instance of Fitmodel class and fill in x values, 
        # y values, and possibly the error bar values in that instance


        # First, we check if the curve number is sensible
        if not isinstance(curvenumber_arg,int):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "set_curve_number"))
            print("The curve number parameter must be an integer. What you supplied is this: {}. Not setting curve number".format(curvenumber_arg))
            return False
        if curvenumber_arg < 0:
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "set_curve_number"))
            print("You supplied a negative curve number: {}. This is not allowed, not setting any curve number".format(curvenumber_arg))
            return False
        if not hasattr(self,self.xaxis_name+"{:d}".format(curvenumber_arg)):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "set_curve_number"))
            print("You are asking for curve number {} which does not exist in the data. Fitting is impossible".format(
                curvenumber_arg))
            return False

        self.PlotNumberChoice.setCurrentText("{:d}".format(curvenumber_arg))
        setattr(self,
                self.fitmodel_instance_name + "{:d}".format(curvenumber_arg),
                Fitmodel(fitfunction_name=self.FitFunctionChoice.currentText(),
                         x_axis_vals=getattr(self, self.xaxis_name + "{:d}".format(curvenumber_arg)),
                         measured_data=getattr(self, self.yaxis_name + "{:d}".format(curvenumber_arg)),
                         errorbars_data=getattr(self, self.err_name + "{:d}".format(curvenumber_arg), None)
                         )
                )
        return True

    def set_starting_parameters(self,supplied_startparams_dict: dict) -> bool:
        """
        Sets the starting parameters for the fitter to be called in this iteration of doFit.  
                
        Parameters
        ----------
        supplied_startparams_dict: dict
            The key:value pairs are always in the form str:float,int where the key 
            is exactly the string name of the parameter defined in the fitting function 
            in fitmodels.py, and the value is the number giving the starting values of that 
            parameter for the fitter.
            
            Whatever parameters from the fit model are not specified will be handled 
            by the automatic parameter estimation routine (which, OK, could be good or bad)
            
        Returns
        -------
        bool
            True if the function finished correctly, False, if there was an error
            Check error messages for explanations of errors
        
        """
    
        # Check if the supplied starting parameters is a dictionary
        if not isinstance(supplied_startparams_dict, dict):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "set_starting_parameters"))
            print("You put something other than a dictionary for the starting parameters. This is not allowed \n")
            return False
        # Check if the values in this dictionary are all numbers (int or float) 
        if not all([isinstance(val,(int,float)) for val in supplied_startparams_dict.values()]):
            print("Message from Class {} function {}".format(self.__class__.__name__, "set_starting_parameters"))
            print("You supplied something other than numbers for startparameters values. This is not allowed \n")
            return False

        # this current_curvenumber should have been registered before with the curve number parameter
        # TODO: Check this bug. Apparently it crashes when the fit model has not been registered
        current_curvenumber = int(self.PlotNumberChoice.currentText())
        for (key,value) in supplied_startparams_dict.items():
            if key in getattr(self,self.fitmodel_instance_name+"{:d}".format(current_curvenumber)).start_paramdict.keys():
                getattr(self,self.fitmodel_instance_name+"{:d}".format(current_curvenumber)).start_paramdict[key] = value
            else:
                print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "set_starting_parameters"))
                print("Warning: your supplied key {} is not among the model parameter keys \n".format(key))
        return True
   
    def set_starting_parameters_limits(self, supplied_startparams_lim_dict: dict) -> bool:
        """
        Sets the limits on teh starting parameters for the fitter to be 
        called in this iteration of doFit.  
                
        Parameters
        ----------
        supplied_startparams_lim_dict: dict
            The key:value pairs are always in the form str:list where the key 
            is exactly the string name of the parameter defined in the fitting function 
            in fitmodels.py, and the value is a list of two either numbers (can be float
            or integer)
            
            Whatever limits are not specified will be filled in by the automatic estimation 
            routine
            
        Returns
        -------
        bool
            True if the function finished correctly, False, if there was an error
            Check error messages for explanations of errors
        
        """
        # check if all startparam limits are dictionaries
        if not isinstance(supplied_startparams_lim_dict, dict):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "set_starting_parameters_limits"))
            print("You put something other than a dictionary for the starting parameters limits. This is not allowed")
            return False
        # check if all values in these dictionaries are lists
        if not all([isinstance(val,list) for val in supplied_startparams_lim_dict.values()]):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "set_starting_parameters_limits"))
            print("You supplied something other than lists for start param limit values. This is not allowed")
            return False
        # check if 
        if not all([(len(val) == 2) for val in supplied_startparams_lim_dict.values()]):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "set_starting_parameters_limits"))
            print("Some of your supplied lists for start param limits are not of length 2.")
            return False
        
        # this current_curvenumber should have been registered before with the curve number parameter
        current_curvenumber = int(self.PlotNumberChoice.currentText())
        current_startparamdict = getattr(self,self.fitmodel_instance_name+"{:d}".format(current_curvenumber)).start_paramdict
        for (key,value) in supplied_startparams_lim_dict.items():
            # Check if the key is in param dict for model and if
            # the values in the list are numbers
            if (key in current_startparamdict) and all([isinstance(q,(int,float)) for q in value]):
                if (value[0] <= current_startparamdict[key]) and (value[1] >= current_startparamdict[key]):
                    getattr(self,self.fitmodel_instance_name+"{:d}".format(current_curvenumber)).start_bounds_paramdict[key] = value
                else:
                    print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "set_starting_parameters_limits"))
                    print("The lower bound must be below the initial value and the upper bounds must be above the initial value. It's not the case now. Not setting this supplied key-value pair for bounds: {}".format((key,value)))
            else:
                print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "set_starting_parameters_limits"))
                print("Your supplied key is not among the model parameter keys or your put something other than numbers as the values for limits. Not setting this key-value pair for bounds: {}".format((key,value)))
        return True


    def set_crop_limits(self,croplimits_arg: list) -> bool: 
        """
        Sets the crop tuple that will be used as limits for fitting. Remember that this
        will not remove the points from the plot! This will only make sure that the 
        points beyond the cropping region are not counted in the fit
                
        Parameters
        ----------
        croplimits_arg: list
            The list of two values (numbers, so int or float). Remember to always specify two values. 
            The left one must be smaller than the right one. Also, one can specify -inf or inf for the 
            left and right limit respectively in order to basically not cut off any data for sure. 
            
            This entry is optional, if one doesn't give it, all data for a give curve 
            are used
            
        Returns
        -------
        bool
            True if the function finished correctly, False, if there was an error
            Check error messages for explanations of errors
        
        """

        # make sure that croplimits is a list
        if not isinstance(croplimits_arg, list):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "set_crop_limits"))
            print("You put something other than a list as crop limits. This is not allowed, not setting any crop limits")
            return False
        # Check if the list contains two elements and if they are numbers

        croplimits_arg = [np.inf if q == "inf" else q for q in croplimits_arg]
        croplimits_arg = [-np.inf if q == "-inf" else q for q in croplimits_arg]

        if not (len(croplimits_arg) == 2 and all([isinstance(q,(int,float)) for q in croplimits_arg])):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "set_crop_limits"))
            print("Either the length of your crop limits argument is not 2 or the values you put in are not numbers. This is not allowed, not setting any crop limits. Here is what you put in: {}".format(croplimits_arg))
            return False
        # Make sure that the first crop limit is strictly smaller than 
        # the second one
        if not croplimits_arg[0] < croplimits_arg[1]:
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "set_crop_limits"))
            print("The first crop limit must always be smaller than the second crop limit. It's not the case now, not setting any crop limits. Here is what you put in: {}".format(croplimits_arg))
            return False

        # this curve number should be registered by now
        current_curve_number = int(self.PlotNumberChoice.currentText())
        getattr(self,self.fitmodel_instance_name+"{:d}".format(current_curve_number)).crop_bounds_list = croplimits_arg
        return True
    
    def set_fit_method(self,fitmethod_arg: str) -> bool:
        """
        Sets the minimization method from scipy.optimize library that will be used for fitting. 
        
        
        Refer to the documentation of scipy.optimize for details. Have a look also in fitterclass.py
        to see what exactly has been implemented at any given time, because this data is used in 
        the do_fit() method of GeneralFitter1D class
        
        This function does not check whether the supplied fit (minimization)
        method actually exists in scipy.optimize! It's up to the user 
        to make sure to not supply nonsense fit methods, or to check 
        this further downstream in fitting
                
        Parameters
        ----------
        fitmethod_arg: str
            The name of the fitting method to use. It wraps the scipy.optimize methods 
            Currently we have "minimize", "least_squares", "basinhopping", "differential_evolution", 
            "shgo", "dual_annealing". "brute_force" is not implemented            
            
            If not given, it will default to "least_squares"
            
            This function does not check whether the supplied fit (minimization)
            method actually exists in scipy.optimize! It's up to the user 
            to make sure to not supply nonsense fit methods, or to check 
            this further downstream in fitting
            
        Returns
        -------
        bool
            True if the function finished correctly, False, if there was an error
            Check error messages for explanations of errors
        
        """
        # we check that the fit method is actually a string
        if not isinstance(fitmethod_arg, str):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "set_fit_method"))
            print("You put something other than a string for fit method. This is not allowed. If other settings are OK, the fitter used will be least_squares")
            return False
        
        current_curve_number = int(self.PlotNumberChoice.currentText())
        getattr(self,self.fitmodel_instance_name+"{:d}".format(current_curve_number)).minimization_method_str = fitmethod_arg
        return True

    def set_fitter_options(self,fitteroptions_arg: dict) -> bool:      
        """
        Feeds the options (as keyword arguments) to scipy.optimize algorithm
        
        Refer to the documentation of scipy.optimize for details. Note that this program does not check 
        whether these options actually make sense for the given scipy.optimize algorithm, it's 
        up to the user to check that out
                        
        Parameters
        ----------
        fitteroptions_arg: dict
            The dictionary is passed directly to the scipy.optimize method as keyword arguments. 
            
        Returns
        -------
        bool
            True if the function finished correctly, False, if there was an error
            Check error messages for explanations of errors
        
        """
        
        # we check that the fit method is actually a dictionary
        if not isinstance(fitteroptions_arg, dict):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "set_fitter_options"))
            print("You put something other than a dictionary for fitter options. This is not allowed. Not setting any fitter options")
            return False
        
        current_curve_number = int(self.PlotNumberChoice.currentText())
        getattr(self,self.fitmodel_instance_name+"{:d}".format(current_curve_number)).fitter_options_dict = fitteroptions_arg
        return True
        
    def set_monte_carlo_runs(self,montecarloruns_dict_arg: dict) -> bool:
        """
        This sets up the self.monte_carlo_inputs dictionary for the fitmodel 
        and it has to be then 
        processed with GeneralFitter1D, I think
        """
        # make sure that montecarloruns_dict_arg is a dict
        if not isinstance(montecarloruns_dict_arg, dict):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "set_monte_carlo_runs"))
            print("You put something other than a dict to specify Monte Carlo runs. This is not allowed, not doing any Monte Carlo in fitting")
            return False
        
        current_curve_number = int(self.PlotNumberChoice.currentText())                
        start_paramdict_fitmodel = getattr(self,self.fitmodel_instance_name+"{:d}".format(current_curve_number)).start_paramdict
        
        for suppliedkey in montecarloruns_dict_arg.keys():
            # check if the parameters supplied for Monte Carlo fitting correspond to the parameter names for the fit model
            # If not, ignore those parameters
            if suppliedkey not in start_paramdict_fitmodel.keys():
                print("Warning from Class {:s} function {:s}".format(self.__class__.__name__, "set_monte_carlo_runs"))
                print("The parameter name {} that you supplied is not among the parameter names for this fitmodel. Ignoring this parameter".format(suppliedkey))
                continue
            # check if for each parameter, the number of Monte Carlo runs is an integer
            if not isinstance(montecarloruns_dict_arg[suppliedkey], int):
                print("Warning from Class {:s} function {:s}".format(self.__class__.__name__, "set_monte_carlo_runs"))
                print("For parameter {} in Monte Carlo, you supplied a non-integer number of runs. This is not allowed, ignoring this parameter".format(suppliedkey))
                continue
            # Check if for each parameter, the number of Monte Carlo runs is not less than 1 (it's meaningless to have less than 1 Monte Carlo run)
            if montecarloruns_dict_arg[suppliedkey] < 1:
                print("Warning from Class {:s} function {:s}".format(self.__class__.__name__, "set_monte_carlo_runs"))
                print("For parameter {} in Monte Carlo, the number of runs you supplied is less than 1. This is not allowed, ignoring this parameter".format(suppliedkey))
                continue
            # If we made it to here, everything is good, and we can save the Monte Carlo setting for this fit parameter    
            getattr(self,self.fitmodel_instance_name+"{:d}".format(current_curve_number)).monte_carlo_inputs[suppliedkey] = montecarloruns_dict_arg[suppliedkey]
        return True

    # This function does the fitting
    def set_perform_fitting(self,emptystring: str) -> bool:
        """
        Runs the fitter

        Parameters
        ----------
        emptystring: str
            As specified, this must be an empty string, and it is ignored. It's here
            only for consistency with all other functions

        Returns
        -------
        bool
            True if the function finished correctly, False, if there was an error
            Check error messages for explanations of errors

        """
        self.process_makefit_button()
        return True

    def get_fit_result(self, arg_int: int) -> bool:
        
        if not isinstance(arg_int, int):
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "get_fit_result"))
            print(
                "Your curve number is not an integer. This is not allowed. Not returning any results \n")
            if self.client_communication_socket is not None:
                error_string_back = helperfunctions.create_JSONRPC_errormessage(-32602,"Curve number not an integer")
                helperfunctions.send_TCPIP_message(self.client_communication_socket,error_string_back,True)
            else:
                print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "get_fit_result"))
                print(
                    "Client communication socket unavailable. Not sending any results to the client \n")
            return False

        if not hasattr(self,self.fitmodel_instance_name+"{:d}".format(arg_int)):
            if self.client_communication_socket is not None:
                error_string_back = helperfunctions.create_JSONRPC_errormessage(-32602,"Curve does not have a fitmodel")
                helperfunctions.send_TCPIP_message(self.client_communication_socket,error_string_back,True)
            else:
                print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "get_fit_result"))
                print(
                    "Client communication socket unavailable. Not sending any results to the client \n")
            return False

        if getattr(self,self.fitmodel_instance_name+"{:d}".format(arg_int)).is_fit_done is False:
            if self.client_communication_socket is not None:
                error_string_back = helperfunctions.create_JSONRPC_errormessage(-32000,"Fit not done")
                helperfunctions.send_TCPIP_message(self.client_communication_socket,error_string_back,True)
            else:
                print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "get_fit_result"))
                print(
                    "Client communication socket unavailable. Not sending any results to the client \n")
            return False

        if getattr(self,self.fitmodel_instance_name+"{:d}".format(arg_int)).is_fit_successful is False:
            if self.client_communication_socket is not None:
                error_string_back = helperfunctions.create_JSONRPC_errormessage(-32000,"Fit not successful")
                helperfunctions.send_TCPIP_message(self.client_communication_socket,error_string_back,True)
            else:
                print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "get_fit_result"))
                print(
                    "Client communication socket unavailable. Not sending any results to the client \n")
            return False

        results_dict = getattr(self,self.fitmodel_instance_name+"{:d}".format(arg_int)).result_paramdict
        results_dict["costfunction"] = getattr(self,self.fitmodel_instance_name+"{:d}".format(arg_int)).result_objectivefunction
        result_string_back = helperfunctions.create_JSONRPC_responsemessage(results_dict)
        if self.client_communication_socket is not None:
            helperfunctions.send_TCPIP_message(self.client_communication_socket, result_string_back, True)
            return True
        else:
            print("Message from Class {:s} function {:s}".format(self.__class__.__name__, "get_fit_result"))
            print(
                "Client communication socket unavailable. Not sending any results to the client \n")
            return False


    def buttonHandler(self,textmessage="blahblahblah"): # we can get the arguments in using functools.partial, or better take no arguments
        print(textmessage)

    def closeEvent(self,event):
        if self.prefitDialogWindow:
            self.prefitDialogWindow.close()

def runPlotter(sysargs):

    HOST = "127.0.0.1"
    #HOST = "134.93.30.62"
    
    # this is the server for one-way communication, no responses
    PORT = 5757
    myServer = TCPIPserver(HOST,PORT)
    myServer.reportedLengthMessage = True
    
    # We want to call this server for two-way communication to send back
    #fit results
    #PORT_TWOWAY = PORT + 1
    #myServerTwoway = TCPIPserver(HOST,PORT_TWOWAY)
    #myServerTwoway.reportedLengthMessage = True


    app = QtWidgets.QApplication(sysargs)
    #w = MainWindow(myServer,myServerTwoway)
    w = MainWindow(myServer)
    #w.show()
    app.exec_()
    if w.prefitDialogWindow:
        w.prefitDialogWindow.close()
    print("done with the plotter")


if __name__ == "__main__":
    runPlotter(sys.argv)
    # TEST
