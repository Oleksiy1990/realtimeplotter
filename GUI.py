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
from interpreter import message_interpreter as mi

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
    result = QtCore.pyqtSignal(object)
    newdata = QtCore.pyqtSignal(str)

class TCP_IP_Worker(QtCore.QRunnable):
    def __init__(self, listener_fn):
        super().__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = listener_fn
        self.signals = WorkerSignals()
        
    @QtCore.pyqtSlot()
    def run(self):
        try:
            self.fn(self.signals.newdata)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))


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

    def __init__(self, aTCPIPserver):
        maxthreads_threadpool = 5

        self.colorpalette = [(255,0,0),(0,255,0),(0,0,255),(255,255,0),(0,255,255),
                (255,0,255),(128,128,128),(128,0,0),(128,128,0),(0,128,0),(128,0,128),
                (0,128,128),(0,0,128)]
        self.yaxis_name = "y"
        self.err_name = "err"
        self.plot_line_name = "data_line"
        self.errorbar_item_name = "errorbar_item"
        self.pen_name = "pen"
        self.errorbar_pen_name = "errpen"

        self.arePlotsCleared = True

        super().__init__()
        mwlayout = QtWidgets.QVBoxLayout()
        #aTCPIPserver.listener_function() # Do not just call it, this must be in a Qt Thread, otherwise it blocks due to the while True statement in it 
        self.graphWidget = pg.PlotWidget()
        self.graphWidget.setBackground('w')
        mwlayout.addWidget(self.graphWidget)

        ClearPlotButton = QtGui.QPushButton("Clear plot")
        ClearDataButton = QtGui.QPushButton("Clear data")
        ClearPlotAndDataBox = QtGui.QHBoxLayout()
        ClearPlotAndDataBox.addWidget(ClearPlotButton)
        ClearPlotAndDataBox.addWidget(ClearDataButton)
        mwlayout.addLayout(ClearPlotAndDataBox)
        
        ClearPlotButton.clicked.connect(partial(self.clear_plot,""))
        ClearDataButton.clicked.connect(partial(self.clear_data,"all"))
        

        self.x = []
        #self.y = []
        #self.x = list(range(100))  # 100 time points
        #self.y1 = [np.sin(q/10) for q in self.x]  # 100 data points
        #self.y2 = [np.sin(q/5) for q in self.x]

        pen = pg.mkPen(color=(255, 0, 0))
        #self.data_line1 =  self.graphWidget.plot(self.x, self.y1,pen=pen, symbol="o") # This returns apparently a PlotDataItem
        #self.data_line2 =  self.graphWidget.plot(self.x, self.y2,pen=pen, symbol="o") # This returns apparently a PlotDataItem
        #self.data_line1.sigClicked.connect(partial(self.buttonHandler,"gparh clicked"))
        mainwidget = QtWidgets.QWidget()
        mainwidget.setLayout(mwlayout)
        #self.setGeometry(50,50,700,700)
        self.setCentralWidget(mainwidget)
        self.show()

        # That's the framework for setting a Qt timer
        #self.timer = QtCore.QTimer()
        #self.timer.setInterval(50)
        #self.timer.timeout.connect(self.update_plot_data)
        #self.timer.start()
      
        self.threadpool = QtCore.QThreadPool()
        self.threadpool.setMaxThreadCount(maxthreads_threadpool)

        myTCP_IP_Worker = TCP_IP_Worker(aTCPIPserver.listener_function_Qt)
        myTCP_IP_Worker.signals.newdata.connect(self.interpret_message)
        self.threadpool.start(myTCP_IP_Worker)


    def interpret_message(self,message):
        interpretation_result = mi(message)
        for res in interpretation_result:
            function_to_call = getattr(self,res[0],"nofunction")
            function_to_call(res[1])
        self.message_processed = True
    
    def nofunction(self,verbatim_message):
        print("Function interpreter.message_interpreter could not determine which function to call based on analyzing the transmitted message. Not calling any function. Here is the message that you transmitted (verbatim): {} \n".format(verbatim_message))

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

    def generate_plot_pointbypoint(self,datapoint):
        """
        data points are supposed to be sent as tuples in the format (x_val,[y1_val,y2_val,...],[y1_err,y2_err,...]). If the length of the tuple is 3, we have error bars, if the length of the tuple is 2, we do not have error bars
        """

        if len(datapoint) == 2:
            (independent_var,dependent_vars) = datapoint
            if len(self.x) == 0: # This means that the array is empty
                self.arePlotsCleared = False
                [setattr(self,self.yaxis_name+f"{idx}",[]) 
                        for idx in range(len(dependent_vars))]
                [setattr(self,self.pen_name+f"{idx}",
                    pg.mkPen(color=self.colorpalette[idx],style=QtCore.Qt.DashLine)) 
                    for idx in range(len(dependent_vars))]
                [setattr(self,self.plot_line_name+f"{idx}",
                    self.graphWidget.plot(symbol="o",
                    pen=getattr(self,"pen{:d}".format(idx)),
                    symbolBrush = pg.mkBrush(self.colorpalette[idx]))) 
                    for idx in range(len(dependent_vars))]
            if self.arePlotsCleared:
                [setattr(self,self.plot_line_name+f"{idx}",
                    self.graphWidget.plot(symbol="o",
                    pen=getattr(self,"pen{:d}".format(idx)),
                    symbolBrush = pg.mkBrush(self.colorpalette[idx]))) 
                    for idx in range(len(dependent_vars))]
            self.x.append(independent_var)
            for idx in range(len(dependent_vars)):
                getattr(self,self.yaxis_name+f"{idx}").append(dependent_vars[idx])
                arrays_toplot = self.convert_to_numpy(self.x,
                        getattr(self,self.yaxis_name+f"{idx}"))
                getattr(self,self.plot_line_name+f"{idx}").setData(*arrays_toplot)


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
                    self.graphWidget.plot(symbol="o",
                    pen=getattr(self,self.pen_name+f"{idx}"),
                    symbolBrush = pg.mkBrush(self.colorpalette[idx]))) 
                    for idx in range(len(dependent_vars))]
            self.x.append(independent_var)
            if self.arePlotsCleared:
                [setattr(self,self.plot_line_name+f"{idx}",
                    self.graphWidget.plot(symbol="o",
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
                if hasattr(self,self.yaxis_name+f"{idx}"):
                    setattr(self,self.yaxis_name+f"{idx}",[])
                else:
                    break
            for idx in range(MAX_CURVES):
                if hasattr(self,self.err_name+f"{idx}"):
                    setattr(self,self.err_name+f"{idx}",[])
                else:
                    break
            self.clear_plot("")
            return None
        else:
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
            except:
                print(f"Error message from Class {self.__class__.__name__} function clear_data: you put an invalid argument. Not clearing any data")
            return None

    def set_axis_labels(self,axis_labels):
        self.graphWidget.setLabels(bottom=axis_labels[0],left=axis_labels[1])
    def set_plot_title(self,plotTitle):
        self.graphWidget.setTitle(title=plotTitle)


    def buttonHandler(self,textmessage="blahblahblah"): # we can get the arguments in using functools.partial, or better take no arguments
        print(textmessage)

def runPlotter(sysargs):

    HOST = "127.0.0.1"
    #HOST = "134.93.88.156"
    PORT = 5757
    myServer = TCPIPserver(HOST,PORT)
    
    app = QtWidgets.QApplication(sysargs)
    w = MainWindow(myServer)
    #w.show()
    app.exec_()
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
