# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 22:20:19 2020

@author: Oleksiy

Not used extensively yet, this is for plotting the excited state evolution given a distribution of Rabi 
frequencies due to different excited state occupations

"""
import distributions as dis
import rabifrequencies as rfr

import numpy as np


def excited_occupation_evolution(t,rabifreq_array,probability_array):
    """
    This is eq. 4.23 from Poulsen thesis 2012 (Aarhus)
    
    """
    cos_argument = np.einsum("i,j->ij",rabifreq_array,t)/2.
    cos_values = np.cos(cos_argument)
    excited_occupation = 0.5*(1-np.einsum("i,ij->j",probability_array,cos_values))
    return excited_occupation


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    n_bar = 20
    numstates = 150
    rabifreq_car = 4e5*2*np.pi
    eta_LD = 0.127
    rabifreq_bsb = np.array([rfr.rabifreq_general(n_start,1,rabifreq_car, eta_LD) for n_start in range(numstates)])
    
    probs = np.array([dis.thermal_probability_avg_n(n, n_bar) for n in range(numstates)])
    print(np.sum(probs))
    #rabifreqs = np.empty(numstates); rabifreqs.fill(rabifreq_car)
    rabifreqs = rabifreq_bsb
    t = np.linspace(0,0.25e-3,1400)
    plt.plot(t,excited_occupation_evolution(t, rabifreqs, probs))
    plt.show()
    
    plt.plot(rabifreqs/(2*np.pi))
    plt.show()
    
    plt.plot(probs)
    plt.show()
    
    
    
    pass
