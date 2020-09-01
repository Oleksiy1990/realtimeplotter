# -*- coding: utf-8 -*-
"""
Created on Fri Aug 28 11:21:29 2020

@author: Oleksiy
"""

class A:
    def __init__(self):
        print("Initialized instance")
        
    def __del__(self):
        print("Deleted instance")
        
    def selfdesctruction(self):
        self.__del__()
        
    def printstuff(self,stuff):
        print(stuff)
        
a1 = A()
a1.printstuff("Hello")
a1.selfdesctruction()
a1.printstuff("Hello 2")