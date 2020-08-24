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

        super().__init__()
        mwlayout = QtWidgets.QVBoxLayout()
        #aTCPIPserver.listener_function() # Do not just call it, this must be in a Qt Thread, otherwise it blocks due to the while True statement in it 
        self.graphWidget = pg.PlotWidget()
        self.graphWidget.setBackground('w')
        mwlayout.addWidget(self.graphWidget)
        #self.graphWidget.setYRange(-1,2)       
        self.Button1 = QtWidgets.QPushButton("1")
        self.Button1.clicked.connect(partial(self.buttonHandler,"some weird test"))
        mwlayout.addWidget(self.Button1)
        

        self.x = []
        self.y = []
        self.x = list(range(100))  # 100 time points
        self.y1 = [np.sin(q/10) for q in self.x]  # 100 data points
        self.y2 = [np.sin(q/5) for q in self.x]

        self.newPlot = pg.PlotItem()
        pen = pg.mkPen(color=(255, 0, 0))
        self.data_line1 =  self.graphWidget.plot(self.x, self.y1,pen=pen, symbol="o") # This returns apparently a PlotDataItem
        self.data_line2 =  self.graphWidget.plot(self.x, self.y2,pen=pen, symbol="o") # This returns apparently a PlotDataItem
        #self.data_line = self.newPlot.plot(self.x, self.y,pen=pen, symbol="o") # This returns apparently a PlotDataItem
        self.data_line1.sigClicked.connect(partial(self.buttonHandler,"gparh clicked"))
        mainwidget = QtWidgets.QWidget()
        mainwidget.setLayout(mwlayout)
        #self.setGeometry(50,50,700,700)
        self.setCentralWidget(mainwidget)
        self.show()
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
        interpretation_result = mi(message) #always return a tuple of 2 entries: the first is the name of the function to call, the second is the data to feed into that function
        function_to_call = getattr(self.__class__,interpretation_result[0],"nofunction")
        function_to_call(self,interpretation_result[1]) # apparently we have to explicitly pass self if we use a function via getattr inside class
    
    def nofunction(self,verbatim_message):
        print("Function interpreter.message_interpreter could not determine which function to call based on analyzing the transmitted message. Not calling any function. Here is the message that you transmitted (verbatim): {:s} \n".format(verbatim_message))

    def showdata(self,data):
        print(data)

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

    def buttonHandler(self,textmessage="blahblahblah"): # we can get the arguments in using functools.partial, or better take no arguments
        print(textmessage)

def runPlotter(sysargs):

    HOST = "127.0.0.1"
    
    PORT = 5757
    myServer = TCPIPserver(HOST,PORT)
    
    app = QtWidgets.QApplication(sysargs)
    w = MainWindow(myServer)
    #w.show()
    app.exec_()
    print("done with the plotter")

if __name__ == "__main__":
    runPlotter(sys.argv)
