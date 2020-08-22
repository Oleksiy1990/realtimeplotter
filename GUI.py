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
import sys  # We need sys so that we can pass argv to QApplication
import os
from random import randint
import numpy as np
from functools import partial

pg.setConfigOptions(crashWarning=True)

class MainWindow(QtGui.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        mwlayout = QtWidgets.QVBoxLayout()
        
        self.graphWidget = pg.PlotWidget()
        self.graphWidget.setBackground('w')
        mwlayout.addWidget(self.graphWidget)
        #self.graphWidget.setYRange(-1,2)       
        self.Button1 = QtWidgets.QPushButton("1")
        self.Button1.clicked.connect(partial(self.buttonHandler,"some weird test"))
        mwlayout.addWidget(self.Button1)
        self.textfield = pg.TextItem(text="Hello, here is some text")
        self.graphWidget.addItem(self.textfield)
        #self.graphWidget = pg.PlotItem()
        self.x = list(range(100))  # 100 time points
        self.y = [np.sin(q/10) for q in self.x]  # 100 data points

        pen = pg.mkPen(color=(255, 0, 0))
        self.data_line =  self.graphWidget.plot(self.x, self.y,pen=pen, symbol="o") # This returns apparently a PlotDataItem
        self.data_line.sigClicked.connect(partial(self.buttonHandler,"gparh clicked"))
        mainwidget = QtWidgets.QWidget()
        mainwidget.setLayout(mwlayout)
        #self.setGeometry(50,50,700,700)
        self.setCentralWidget(mainwidget)
        #self.timer = QtCore.QTimer()
        #self.timer.setInterval(50)
        #self.timer.timeout.connect(self.update_plot_data)
        #self.timer.start()
        
    def update_plot_data(self):

        self.x = self.x[1:]  # Remove the first y element.
        self.x.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.

        self.y = self.y[1:]  # Remove the first 
        self.y.append(np.sin(self.x[-1]/10))  # Add a new random value.

        self.data_line.setData(self.x, self.y)  # Update the data.

    def buttonHandler(self,textmessage="blahblahblah"): # we can get the arguments in using functools.partial, or better take no arguments
        print(textmessage)

def runPlotter(sysargs):
    app = QtWidgets.QApplication(sysargs)
    w = MainWindow()
    w.show()
    app.exec_()
    print("done with the plotter")

if __name__ == "__main__":
    runPlotter(sys.argv)
