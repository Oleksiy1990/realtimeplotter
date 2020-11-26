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
from interpreter import message_interpreter
from fitterclass import GeneralFitter1D, PrefitterDialog
import fitmodelclass as fm
import helperfunctions

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

    def __init__(self, aTCPIPserver,aTCPIPServerTwoway):
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
        self.yaxis_name = "y"
        self.err_name = "err" 
        self.plot_line_name = "data_line"
        self.fitplot_line_name = "fit_line"
        self.errorbar_item_name = "errorbar_item"
        self.pen_name = "pen"
        self.errorbar_pen_name = "errpen"
        self.fitmodel_instance_name = "fitmodel"
        self.fitmethod_name = "differential_evolution"

        self.all_instance_attribute_names = [self.yaxis_name,
                self.err_name,
                self.plot_line_name,
                self.fitplot_line_name,
                self.errorbar_item_name,
                self.pen_name,
                self.errorbar_pen_name,
                self.fitmodel_instance_name]

        self.x = [] # This is the x-axis for all plots
        # NOTE: Maybe we will have to change this so that plots with different 
        #numbers of x-axis points can be processed uniformly 


        # This is the number of datasets in the current state of the class instance
        self.num_datasets = 0
        self.arePlotsCleared = True
        self.prefitDialogWindow = None

        # the main window is the one holding the plot, and some buttons below. 
        #we make it a vertical box QVBoxLayout, then in this vertical box structure
        #horizontal boxes can be added for buttons, fields, etc. 
        mainwindow_layout = QtWidgets.QVBoxLayout()
        
        # The main field for plotting, which is taken from pyqtgraph, will be called 
        #graphWidget (instance of pyqtgraph.PlotWidget() )
        self.graphWidget = pg.PlotWidget() 
        self.graphWidget.setBackground('w')
        #TODO Get the legend to work
        #self.graphWidget.addLegend()
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

        # Text box at the bottom for displaying fit results to the user
        self.TextBoxForOutput = QtGui.QTextEdit()
        self.TextBoxForOutput.setReadOnly(True)
        self.TextBoxForOutput.setFontPointSize(12.)
        #self.TextBoxForOutput.setPlainText("Hello hello \nHello once again")
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

    def interpret_message(self,message):
        """
        Message is supposed to be a string. 
        The result is a list of tuples. Each tuple has the form 
        ("function name",argument)
        """
        interpretation_result = message_interpreter(message)
        for res in interpretation_result:
            function_to_call = getattr(self,res[0],"nofunction")
            function_to_call(res[1])
        self.message_processed = True
    
    def process_fitresults_call(self,arg_tuple):
        (lock,sender_function,curve_number) = arg_tuple
        #TODELETE
        print("Len arg tuple: ",len(arg_tuple))
        print("Curve number: ",curve_number)
        doesCurveExist = hasattr(self,self.yaxis_name+"{:d}".format(curve_number))
        if doesCurveExist is False:
            print("Message from Class {:s} function process_fitresults_call: You requested fit results for curve {}, but this curve does not exist.".format(self.__class__.__name__,curve_number))
            sender_function(message_string="nocurve")
            lock.release()
            return None
        doesFitModelExist = hasattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number))
        if doesFitModelExist is False:
            sender_function(message_string="nofit")
            lock.release()
            return None
        doesFitExist = getattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number)).fit_isdone
        if doesFitExist is False:
            sender_function(message_string="nofit")
            lock.release()
            return None
        isFitSuccessful = getattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number)).fit_issuccessful
        if isFitSuccessful is False:
            sender_function(message_string="nofitsuccess")
            lock.release()
            return None
        
        message_fitresults = ""
        for (key,val) in getattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number)).fit_function_paramdict.items():
            message_fitresults += "{:s} : {:.10f},".format(key,val)
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
            if result_check_settings:
                setattr(self,
                    self.fitmodel_instance_name+"{:d}".format(curve_number),
                    fm.Fitmodel(fitfunction_name,curve_number,
                        *result_check_settings))
            else:
                print("Message from Class {:s} function process_MakeFit_button: result_check_settings is False, meaning that the data cannot be molded into the correct format to create Fitmodel instance. Check the data".format(self.__class__.__name__))
                return None

        aFitter = GeneralFitter1D(getattr(self,self.fitmodel_instance_name+"{:d}".format(curve_number)))
        aFitter.setupFit(opt_method=self.fitmethod_string)
        # TODO: make the opt_method adjustable from the GUI itself and as one of the parameters of the command string via TCP/IP
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
            # replot the measured data points
            getattr(self,self.plot_line_name+"{:d}".format(curve_number)).setData(*measured_data_array[0:2])

            # if the fit plot aleady exists, clear it, because we don't want
            #multiple plots piling up on each other
            if hasattr(self,self.fitplot_line_name+"{:d}".format(curve_number)):
                getattr(self,self.fitplot_line_name+"{:d}".format(curve_number)).clear()
            
            # finally make a fit plot line and plot the data to it
            setattr(self,self.fitplot_line_name+"{:d}".format(curve_number),
                self.graphWidget.plot(symbol=None,pen=getattr(self,"pen{:d}".format(curve_number)),
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

    # This function is for real-time plotting of data points, 
    #just as they come in through TCP/IP
    def generate_plot_pointbypoint(self,datapoint):
        """
        data points are supposed to be sent as tuples in the format (x_val,[y1_val,y2_val,...],[y1_err,y2_err,...]). If the length of the tuple is 3, we have error bars, if the length of the tuple is 2, we do not have error bars
        """

        if len(datapoint) == 2:
            (independent_var,dependent_vars) = datapoint
            if len(self.x) == 0: # This means that the array is empty
                self.arePlotsCleared = False
                [setattr(self,self.yaxis_name+"{:d}".format(idx),[]) 
                        for idx in range(len(dependent_vars))]
                [setattr(self,self.pen_name+"{:d}".format(idx),
                    pg.mkPen(color=self.colorpalette[idx],style=QtCore.Qt.DashLine)) 
                    for idx in range(len(dependent_vars))]
                [setattr(self,self.plot_line_name+"{:d}".format(idx),
                    self.graphWidget.plot(symbol="o",name="C{:d}".format(idx),
                    pen=getattr(self,"pen{:d}".format(idx)),
                    symbolBrush = pg.mkBrush(self.colorpalette[idx]))) 
                    for idx in range(len(dependent_vars))]
            if self.arePlotsCleared:
                [setattr(self,self.plot_line_name+"{:d}".format(idx),
                    self.graphWidget.plot(symbol="o",name="C{:d}".format(idx),
                    pen=getattr(self,"pen{:d}".format(idx)),
                    symbolBrush = pg.mkBrush(self.colorpalette[idx]))) 
                    for idx in range(len(dependent_vars))]
            self.x.append(independent_var)
            for idx in range(len(dependent_vars)):
                getattr(self,self.yaxis_name+"{:d}".format(idx)).append(dependent_vars[idx])
                arrays_toplot = self.convert_to_numpy(self.x,
                        getattr(self,self.yaxis_name+"{:d}".format(idx)))
                getattr(self,self.plot_line_name+"{:d}".format(idx)).setData(*arrays_toplot)

            self.num_datasets = len(dependent_vars)


        if len(datapoint) == 3:
            (independent_var,dependent_vars,errorbar_vars) = datapoint
            if len(self.x) == 0: # This means that the array is empty
                self.arePlotsCleared = False
                [setattr(self,self.yaxis_name+f"{idx}",[]) 
                        for idx in range(len(dependent_vars))]
                [setattr(self,self.err_name+f"{idx}",[]) 
                        for idx in range(len(dependent_vars))]
                [setattr(self,self.pen_name+f"{idx}",pg.mkPen(color=self.colorpalette[idx],
                    style=QtCore.Qt.DashLine)) for idx in range(len(dependent_vars))]
                [setattr(self,self.errorbar_pen_name+f"{idx}",
                    pg.mkPen(color=self.colorpalette[idx],
                    style=QtCore.Qt.SolidLine)) for idx in range(len(dependent_vars))]
                [setattr(self,self.plot_line_name+f"{idx}",
                    self.graphWidget.plot(symbol="o",name="C{:d}".format(idx),
                    pen=getattr(self,self.pen_name+f"{idx}"),
                    symbolBrush = pg.mkBrush(self.colorpalette[idx]))) 
                    for idx in range(len(dependent_vars))]
            self.x.append(independent_var)
            if self.arePlotsCleared:
                [setattr(self,self.plot_line_name+f"{idx}",
                    self.graphWidget.plot(symbol="o",name="C{:d}".format(idx),
                    pen=getattr(self,self.pen_name+f"{idx}"),
                    symbolBrush = pg.mkBrush(self.colorpalette[idx]))) 
                    for idx in range(len(dependent_vars))]

            for idx in range(len(dependent_vars)):
                getattr(self,self.yaxis_name+f"{idx}").append(dependent_vars[idx])
                getattr(self,self.err_name+f"{idx}").append(errorbar_vars[idx])
                arrays_toplot = self.convert_to_numpy(self.x,getattr(self,self.yaxis_name+f"{idx}"),getattr(self,self.err_name+f"{idx}"))
                setattr(self,self.errorbar_item_name+f"{idx}",
                        pg.ErrorBarItem(x = arrays_toplot[0],y =arrays_toplot[1],
                        top = arrays_toplot[2],bottom =arrays_toplot[2],
                        pen=getattr(self,self.errorbar_pen_name+f"{idx}")))
                self.graphWidget.addItem(getattr(self,self.errorbar_item_name+f"{idx}"))
                getattr(self,self.plot_line_name+f"{idx}").setData(*arrays_toplot[0:2])

            self.num_datasets = len(dependent_vars)


    def clear_plot(self,dummyargument):
        """
        This only clear the visual from the plot, it doesn't clear the saved data
        """
        self.graphWidget.clear()
        self.arePlotsCleared = True

    def clear_data(self,data_line_name_string):
        if data_line_name_string == "all":
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
            return None
        # TODO maybe implement the idea of deleting curves one by one
        else:
            return None # for now, so that it doesn't fail
            try:
                curve_to_delete = int(data_line_name_string)
                if hasattr(self,self.yaxis_name+f"{curve_to_delete}"):
                    setattr(self,self.yaxis_name+f"{curve_to_delete}",[])
                    #getattr(self.self.plot_line_name+f"{curve_to_delete}").removeItem()
                    self.graphWidget.removeItem(getattr(self,self.plot_line_name+f"{curve_to_delete}"))
                else:
                    print("You gave a non-existent curve number, it cannot be deleted, not doing anything")
                if hasattr(self,self.err_name+f"{curve_to_delete}"):
                    setattr(self,self.err_name+f"{curve_to_delete}",[])
                    self.graphWidget.removeItem(getattr(self,self.err_name+f"{curve_to_delete}"))
                self.num_datasets -= 1
            except:
                print(f"Error message from Class {self.__class__.__name__} function clear_data: you put an invalid argument. Not clearing any data")
            return None

    def set_axis_labels(self,axis_labels):
        self.graphWidget.setLabels(bottom=axis_labels[0],left=axis_labels[1])
    def set_plot_title(self,plotTitle):
        self.graphWidget.setTitle(title=plotTitle)
    # TODO write the correct function for setting the legends
    def set_plot_legend(self,legendlabels):
        pass
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


class OldFunctions:

    def add_plot_data(self,datapoint):
        self.x.append(datapoint[0])
        self.y.append(datapoint[1])
        self.data_line.setData(self.x,self.y)

    def update_plot_data(self):

        self.x = self.x[1:]  # Remove the first y element.
        self.x.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.

        self.y = self.y[1:]  # Remove the first 
        self.y.append(np.sin(self.x[-1]/10))  # Add a new random value.

        self.data_line.setData(self.x, self.y)  # Update the data.

if __name__ == "__main__":
    runPlotter(sys.argv)
    # TEST
