import numpy as np
import scipy.signal as spsig

########################  sinewave model
def sinewave_base(fitparams,independent_var):
    """
    fitparams = [frequency, amplitude, phase, vertical offset]
    """
    return fitparams[1]*np.sin(2*np.pi*fitparams[0]*independent_var + fitparams[2]) + fitparams[3]

def sinewave(fitparams,independent_var,measured_data,errorbars):
    """
    fitparams = [frequency, amplitude, phase, vertical offset]
    """
    return (sinewave_base(fitparams,independent_var) - measured_data)/errorbars

def sinewave_check(fitparams,return_fitparam_empty_dict = False):
    if len(fitparams) == 4:
        return True
    else:
        return False

def sinewave_paramdict():
    fitparam_dict = {"frequency":None, "amplitude":None, "phase":None, "verticaloffset":None}
    return fitparam_dict

def sinewave_prefit(independent_var, measured_data, errorbars, fitparam_dict, fitparam_bounds_dict, low_pts=5,high_pts=5,num_periods=5):
    """
    This requires the x-values, y-values, and the error bars (although error bars are not really necessary 
    but it's just for uniformity, one can simply set them all to 1.

    It also requires fitparam_dict and fitparam_bounds_dict. It will look if any values in fitparam_dict have already been set 
    and use those params, and estimate the other params as well as it can. It will also set the fitparameter bounds so that those can be used in the fitter. 
    """
   
    if not fitparam_dict:
        print("Message from sinewave_prefit: You did not supply a dictionary of parameters to put the prefit into. Prefitting impossible, not returning any dictionaries for fitting and plotting")
        return None

    if not fitparam_bounds_dict:
        print("Message from sinewave_prefit: You did not supply a dictionary of parameter bounds to put the prefit into. Prefitting impossible, not returning any dictionaries for fitting and plotting")
        return None

    # first we estimate the amplitude
    if fitparam_dict["amplitude"]:
        amplitude_est = fitparam_dict["amplitude"]
    else:
        low_est = np.mean(np.partition(measured_data,low_pts)[0:low_pts])
        high_est = -1*np.mean(np.partition(-1*measured_data,high_pts)[0:high_pts])
        amplitude_est = 0.5*(high_est-low_est)
    
    amplitude_bounds_est = [0,2*amplitude_est]
    fitparam_dict["amplitude"] = amplitude_est
    fitparam_bounds_dict["amplitude"] = amplitude_bounds_est
    
    # now we estimate the verticaloffset
    if fitparam_dict["verticaloffset"]:
        vertical_offset_est = fitparam_dict["verticaloffset"]
        vertical_offset_bounds_est = [vertical_offset_est - 0.3*amplitude_est,vertical_offset_est + 0.3*amplitude_est]
    else:
        low_est = np.mean(np.partition(measured_data,low_pts)[0:low_pts])
        high_est = -1*np.mean(np.partition(-1*measured_data,high_pts)[0:high_pts])
        vertical_offset_est = low_est+amplitude_est
        vertical_offset_bounds_est = [low_est,high_est]
   
    fitparam_dict["verticaloffset"] = vertical_offset_est
    fitparam_bounds_dict["verticaloffset"] = vertical_offset_bounds_est
    
    # now we estimate the phase
    if fitparam_dict["phase"]:
        phase_est = fitparam_dict["phase"]
    else:
        phase_est = 1e-5 #this is just effectively 0
    phase_bounds_est = [-np.pi,np.pi]
    
    fitparam_dict["phase"] = phase_est
    fitparam_bounds_dict["phase"] = phase_bounds_est

    # now we estimate the frequency
    if fitparam_dict["frequency"]:
        frequency_est = fitparam_dict["frequency"]
    else:
        frequency_est = num_periods/(np.max(independent_var)-np.min(independent_var))
    frequency_bounds_est = [0.5/(np.max(independent_var)-np.min(independent_var)),
                            0.5*len(independent_var)/(np.max(independent_var)-np.min(independent_var))]
   
    fitparam_dict["frequency"] = frequency_est
    fitparam_bounds_dict["frequency"] = frequency_bounds_est

    return (fitparam_dict,fitparam_bounds_dict)




########################### damped sinewave model

def damped_sinewave_base(fitparams,independent_var):
    """
    fitparams = [frequency, amplitude, phase, vertical offset, damping constant]
    """
    return fitparams[1]*np.sin(2*np.pi*fitparams[0]*independent_var + fitparams[2])*np.exp(-independent_var/fitparams[4]) + fitparams[3]

def damped_sinewave(fitparams,independent_var,measured_data,errorbars):
    """
    fitparams = [frequency, amplitude, phase, vertical offset, damping constant]
    """
    return (damped_sinewave_base(fitparams,independent_var) - measured_data)/errorbars

def damped_sinewave_check(fitparams):
    if len(fitparams) == 5:
        return True
    else:
        return False

def damped_sinewave_paramdict():
    fitparam_dict = {"frequency":None, "amplitude":None, "phase":None, "verticaloffset":None, "dampingconstant":None}
    return fitparam_dict

def damped_sinewave_prefit(independent_var,measured_data,errorbars,fitparam_dict,fitparam_bounds_dict,low_pts = 5, high_pts = 5, num_periods = 5):

    """
    This requires the x-values, y-values, and the error bars (although error bars are not really necessary 
    but it's just for uniformity, one can simply set them all to 1.

    It also requires fitparam_dict and fitparam_bounds_dict. It will look if any values in fitparam_dict have already been set 
    and use those params, and estimate the other params as well as it can. It will also set the fitparameter bounds so that those can be used in the fitter. 
    """
   
    if not fitparam_dict:
        print("Message from damped_sinewave_prefit: You did not supply a dictionary of parameters to put the prefit into. Prefitting impossible, not returning any dictionaries for fitting and plotting")
        return None

    if not fitparam_bounds_dict:
        print("Message from damped_sinewave_prefit: You did not supply a dictionary of parameter bounds to put the prefit into. Prefitting impossible, not returning any dictionaries for fitting and plotting")
        return None


    # first we estimate the amplitude
    if fitparam_dict["amplitude"]:
        amplitude_est = fitparam_dict["amplitude"]
    else:
        # we take the average of the five highest points and five lowest points, take the difference and divide by 2. 
        #That is the guess of the amplitude
        low_est = np.mean(np.partition(measured_data,low_pts)[0:low_pts])
        high_est = -1*np.mean(np.partition(-1*measured_data,high_pts)[0:high_pts])
        amplitude_est = 0.5*(high_est-low_est)
    
    amplitude_bounds_est = [0,2*amplitude_est]
    fitparam_dict["amplitude"] = amplitude_est
    fitparam_bounds_dict["amplitude"] = amplitude_bounds_est
    
    # now we estimate the verticaloffset
    if fitparam_dict["verticaloffset"]:
        vertical_offset_est = fitparam_dict["verticaloffset"]
        vertical_offset_bounds_est = [vertical_offset_est - 0.3*amplitude_est,vertical_offset_est + 0.3*amplitude_est]
    else:
        # vertical offset is just the mean of the data
        vertical_offset_est = np.mean(measured_data)
        vertical_offset_bounds_est = [vertical_offset_est - 0.3*amplitude_est,vertical_offset_est + 0.3*amplitude_est]
   
    fitparam_dict["verticaloffset"] = vertical_offset_est
    fitparam_bounds_dict["verticaloffset"] = vertical_offset_bounds_est
    
    # now we estimate the phase
    if fitparam_dict["phase"]:
        phase_est = fitparam_dict["phase"]
    else:
        # set the phase estimate effectively to 0
        phase_est = 1e-5 
    phase_bounds_est = [-np.pi,np.pi]
    
    fitparam_dict["phase"] = phase_est
    fitparam_bounds_dict["phase"] = phase_bounds_est

    # now we estimate the frequency
    if fitparam_dict["frequency"]:
        frequency_est = fitparam_dict["frequency"]
    else:
        # We have to somehow guess the frequency. This is a bit difficult with no data at all, that's why there's that 
        #num_periods parameter at the beginning, which is like, roughly how many periods of the wave do we expect in the 
        #dataset. I just set it at 5 as a wild guess
        frequency_est = num_periods/(np.max(independent_var)-np.min(independent_var))
    frequency_bounds_est = [0.5/(np.max(independent_var)-np.min(independent_var)),
                            0.5*len(independent_var)/(np.max(independent_var)-np.min(independent_var))]
   
    fitparam_dict["frequency"] = frequency_est
    fitparam_bounds_dict["frequency"] = frequency_bounds_est

    # The automatic estimate is not good yet, I need to find a good way to estimate it
    if fitparam_dict["dampingconstant"]:
        dampingconstant_est = fitparam_dict["dampingconstant"]
    else:
        dampingconstant_est = num_periods/frequency_est
    dampingconstant_bounds_est = [1e-6,1e20]
   
    fitparam_dict["dampingconstant"] = dampingconstant_est
    fitparam_bounds_dict["dampingconstant"] = dampingconstant_bounds_est
    
    return (fitparam_dict,fitparam_bounds_dict)


def gaussian_base(fitparams,independent_var):
    """
    fitparams = [height, center, sigma, vertical offset]
    defined in the actual normal distribution sense, not like 1/e^2 in optics
    there is NO normalization factor in front, 1/sigma*sqrt(2*pi). Normalization doesn't really matter for us here, and in this manner the height really determines the height of the peak above the baseline. If height = 1, the height of the peak is 1
    """
    return fitparams[0]*np.exp(-0.5*np.power(independent_var - fitparams[1],2.)/np.power(fitparams[2],2.)) + fitparams[3]

def gaussian(fitparams,independent_var,measured_data,errorbars):
    """
    fitparams = [height, center, sigma, vertical offset]
    """
    return (gaussian_base(fitparams,independent_var) - measured_data)/errorbars

def gaussian_check(fitparams,return_fitparam_empty_dict = False):
    if len(fitparams) == 4:
        return True
    else:
        return False

def gaussian_paramdict():
    fitparam_dict = {"height":None, "center":None, "sigma":None, "verticaloffset":None}
    return fitparam_dict

def gaussian_prefit(independent_var, measured_data, errorbars,
        fitparam_dict, fitparam_bounds_dict, 
        fraction_frontback=0.1,vertoffset_deviation_fraction = 0.3,
        num_periods=5):
    """
    This requires the x-values, y-values, and the error bars (although error bars are not really necessary 
    but it's just for uniformity, one can simply set them all to 1.

    It also requires fitparam_dict and fitparam_bounds_dict. It will look if any values in fitparam_dict have already been set 
    and use those params, and estimate the other params as well as it can. It will also set the fitparameter bounds so that those can be used in the fitter. 
    """
   
    if not fitparam_dict:
        print("Message from sinewave_prefit: You did not supply a dictionary of parameters to put the prefit into. Prefitting impossible, not returning any dictionaries for fitting and plotting")
        return None

    if not fitparam_bounds_dict:
        print("Message from sinewave_prefit: You did not supply a dictionary of parameter bounds to put the prefit into. Prefitting impossible, not returning any dictionaries for fitting and plotting")
        return None

    # first we estimate the vertical offset by looking at the average of the data at the edges, which is assumed to be away from the Gaussian peak
    if fitparam_dict["verticaloffset"]:
        vertoffset_est = fitparam_dict["verticaloffset"]
    else:
        arraylen_fraction = int(len(measured_data)*fraction_frontback)
        vertoffset_est = np.mean(np.union1d(measured_data[0:arraylen_fraction],measured_data[-arraylen_fraction:]))
    
    vertoffset_deviation = np.abs(vertoffset_est*vertoffset_deviation_fraction)
    vertoffset_bounds_est = [vertoffset_est - vertoffset_deviation,
           vertoffset_est + vertoffset_deviation]
    fitparam_dict["verticaloffset"] = vertoffset_est
    fitparam_bounds_dict["verticaloffset"] =  vertoffset_bounds_est
    
    data_subtracted_background = measured_data - vertoffset_est
    # now we estimate the position of the center
    if fitparam_dict["center"]:
        center_est = fitparam_dict["center"]
    else:
        # we use the Savitzky-Golay filter from scipy.filter, and then find the 
        #location of the max of the filtered array
        filtered_savgol = spsig.savgol_filter(data_subtracted_background,10,3)
        filtered_savgol_abs = np.abs(filtered_savgol)
        center_est = np.argmax(filtered_savgol_abs)  
    center_bounds_est = [0,len(measured_data)-1]
    fitparam_dict["center"] = center_est
    fitparam_bounds_dict["center"] = center_bounds_est

    
    # now we estimate the height
    #note that the height can be negative, in which case the Gaussian points downwards
    if fitparam_dict["height"]:
        height_est = fitparam_dict["height"]
    else:
        # basically the height is just the value of the function at the maximum point 
        #(evaluated after smoothing with the Savitzky-Golay filter)
        filtered_savgol = spsig.savgol_filter(data_subtracted_background,10,3)
        height_est = filtered_savgol[center_est]
    height_bounds_est = [height_est - 0.3*height_est, height_est + 0.3*height_est].sort()   
    fitparam_dict["height"] = height_est
    fitparam_bounds_dict["height"] = height_bounds_est
    

    # now we estimate the frequency
    if fitparam_dict["sigma"]:
        sigma_est = fitparam_dict["sigma"]
    else:
        # we do the max likelihood estimation of the sigma
        sum_squared_differences = np.sum(np.power(data_subtracted_background - center_est),2.)
        sigma_est = np.sqrt(sum_squared_differences/len(data_subtracted_background))
   
    sigma_bounds_est = [sigma_est/3.,3*sigma_est].sort()
    fitparam_dict["sigma"] = sigma_est
    fitparam_bounds_dict["sigma"] = sigma_bounds_est

    return (fitparam_dict,fitparam_bounds_dict)



