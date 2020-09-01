# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 18:13:01 2020

@author: Oleksiy

Generating the Rabi frequencies for different sideband transitions given the carrier Rabi frequency

"""
import numpy as np
from scipy.special import genlaguerre

"""
Approximations for driving the first sideband only, 
Lamb-Dicke regime
"""
def rabifreq_rsb(n_start,rabifreq_car,Lamb_Dicke):
    return Lamb_Dicke*np.sqrt(n_start)*rabifreq_car
def rabifreq_bsb(n_start,rabifreq_car,Lamb_Dicke):
    return Lamb_Dicke*np.sqrt(n_start+1)*rabifreq_car

def rabifreq_general(n_start,delta_n,rabifreq_car,Lamb_Dicke):
    if delta_n == 0:
        return rabifreq_car
    n_lesser = np.min([n_start,n_start + delta_n])
    n_greater = np.max([n_start,n_start + delta_n])
    if n_lesser < 0:
        return 0
    laguerre_polynomial = genlaguerre(n_lesser,np.abs(delta_n))
    laguerre_factor = laguerre_polynomial(np.power(Lamb_Dicke,2.))
    sqrt_factor = np.sqrt(np.math.factorial(n_lesser)/np.math.factorial(n_greater))
    result = rabifreq_car*np.exp(-0.5*np.power(Lamb_Dicke,2.))*np.power(Lamb_Dicke,np.abs(delta_n))*sqrt_factor*laguerre_factor
    return result
if __name__ == "__main__":
    import matplotlib.pyplot as plt
    n_lesser = np.linspace(0,99,100,dtype=np.int)
    delta_n = 1
    print(n_lesser)
    factor = [np.sqrt(np.math.factorial(q)/np.math.factorial(q+delta_n)) for q in n_lesser]
    laguerre_polynomial = [genlaguerre(n,np.abs(delta_n)) for n in n_lesser]
    laguerre_factor = [lag(np.power(0.12,2.)) for lag in laguerre_polynomial]
    plt.plot(n_lesser,np.array(laguerre_factor)*np.array(factor))
    plt.show()
