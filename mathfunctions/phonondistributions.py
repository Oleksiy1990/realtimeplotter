# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 17:24:44 2020

@author: Oleksiy


These are phonon number distributions for ions
"""

import numpy as np
from scipy import constants


def thermal_probability_avg_n(n,avg_n):
    """
    Poulsen thesis 2012 Aarhus, eq. 4.18
    Deal with natural logs in order to not get numerical problems due to large powers
    """
    logprob = n*np.log(avg_n) - (n + 1)*np.log(avg_n + 1)
    #return np.clip(np.exp(logprob) - 1e-10,0,1)
    return np.exp(logprob)

def thermal_probability_temp(n,temperature,secular_frequency,n_max = 500):
    """
    Poulsen thesis 2012 Aarhus, eq. 4.24
    """
    beta = 1/(constants.value("Boltzmann constant")*temperature)
    weighting_factor = np.exp(-beta*(n + 0.5)*constants.value("Planck constant")*secular_frequency)
    partition_function = np.sum([np.exp(-beta*(n_dummy + 0.5)*constants.value("Planck constant")*secular_frequency) for n_dummy in range(n_max)])
    return weighting_factor/partition_function

def displaced_probability(n,alpha):
    """
    RabiMCMC_V3 document eq. 6. This is the probability of having 
    n phonons in a displaced coherent state with parameter alpha
    """
    alpha_absolute_square = np.power(np.abs(alpha),2.)
    return np.exp(-alpha_absolute_square)*np.power(alpha_absolute_square,n)/np.math.factorial(n)

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    temp = 1e-3
    secular_freq = 2e6
    n_bar = 20
    n_vals = np.linspace(0,100,100)
    plt.plot(n_vals,thermal_probability_temp(n_vals,temp,secular_freq))
    plt.show()
    plt.plot(n_vals,thermal_probability_avg_n(n_vals, n_bar))
    plt.show()
    
    


