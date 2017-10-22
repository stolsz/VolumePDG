# -*- coding:Utf-8 -*-
'''
Created on 2014-07-26

@author: Simon T-L
'''
# Fichier contenant des fonctions et classes utiles.
#
# Quelques unes ont ete prise dans la librairie Statistical Analyst de ESRI, mais deplacees 
# ici car les scripts executes dans ArcMap ne vont pas chercher les module avec PYTHONPATH
# il semble...

################## Classes ##########################

class ScriptError(Exception):
    """Send an error message to the application history window.  
    Inherits from the Python Exception Class.  
    See: www.python.org/doc/current/tut/node10.html for more
    information about custom exceptions.

    INPUTS:
    value (str): error message to be delivered.

    METHODS:
    __str__: returns error message for printing.
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

class Gen:
    """A generic object."""
    def __init__(self):
        pass
    def add(self, name, value):
        self.__dict__[name] =  value
        
