# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 14:39:39 2020

@author: Oleksiy

Writing the function definition for fit models in least squares optimization
We need to find the way to import these functions smartly, either by their normal function names, or possibly
with string versions of their names, and then getattr() and so on
"""

import numpy as np


def sinewave(fitparams,independent_var,measured_data):
    """
    fitparams = [frequency, amplitude, phase, vertical offset]
    """
    return fitparams[1]*np.sin(2*np.pi*fitparams[0]*independent_var + fitparams[2]) + fitparams[3] - measured_data
def sinewave_e(fitparams,independent_var,measured_data,errorbars):
    """
    fitparams = [frequency, amplitude, phase, vertical offset]
    """
    return (fitparams[1]*np.sin(2*np.pi*fitparams[0]*independent_var + fitparams[2]) + fitparams[3] - measured_data)/errorbars
def sinewave_base(fitparams,independent_var):
    """
    fitparams = [frequency, amplitude, phase, vertical offset]
    """
    return fitparams[1]*np.sin(2*np.pi*fitparams[0]*independent_var + fitparams[2]) + fitparams[3]
def sinewave_check(fitparams):
    if len(fitparams) == 4:
        return True
    else:
        return False
def sinewave_prefit(independent_var,measured_data,errorbars,low_pts=5,high_pts=5,num_periods=5):
    low_est = np.mean(np.partition(measured_data,low_pts)[0:low_pts])
    high_est = -1*np.mean(np.partition(-1*measured_data,high_pts)[0:high_pts])
    amplitude_est = 0.5*(high_est-low_est)
    vertical_offset_est = low_est+amplitude_est
    phase_est = 1e-5 #this is just effectively 0
    frequency_est = num_periods/(independent_var[-1]-independent_var[0])
    
    fitparams_est = [frequency_est,amplitude_est,phase_est,vertical_offset_est]
    return fitparams_est

def damped_sinewave(fitparams,independent_var,measured_data):
    """
    fitparams = [frequency, amplitude, phase, vertical offset, damping constant]
    """
    return fitparams[1]*np.sin(2*np.pi*fitparams[0]*independent_var + fitparams[2])*np.exp(-independent_var/fitparams[4]) + fitparams[3] - measured_data
def damped_sinewave_e(fitparams,independent_var,measured_data,errorbars):
    """
    fitparams = [frequency, amplitude, phase, vertical offset, damping constant]
    """
    return (fitparams[1]*np.sin(2*np.pi*fitparams[0]*independent_var + fitparams[2])*np.exp(-independent_var/fitparams[4]) + fitparams[3] - measured_data)/errorbars
def damped_sinewave_base(fitparams,independent_var):
    """
    fitparams = [frequency, amplitude, phase, vertical offset, damping constant]
    """
    return fitparams[1]*np.sin(2*np.pi*fitparams[0]*independent_var + fitparams[2])*np.exp(-independent_var/fitparams[4]) + fitparams[3]
def damped_sinewave_check(fitparams):
    if len(fitparams) == 5:
        return True
    else:
        return False
