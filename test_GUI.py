import GUI
import pytest
from pytestqt import qtbot
import json
import sys
from PyQt5 import QtWidgets
from socketserver import TCPIPserver

@pytest.fixture
def myMainWindow(qtbot):

    qtbot.addWidget(GUI.MainWindow(TCPIPserver("localhost",10000),
            TCPIPserver("localhost",10001),is_testing=False))

@pytest.mark.parametrize("input_clear_data,expected_clear_data",[
    ("all",True),
    ("blah",False),
    (1,False)
    ])
    

def test_Mainwindow_clear_data(myMainWindow,
        input_clear_data,
        expected_clear_data):
    assert myMainWindow.clear_data(input_clear_data) == expected_clear_data
