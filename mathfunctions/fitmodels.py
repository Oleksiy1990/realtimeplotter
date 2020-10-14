import numpy as np

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
    phase_bounds_est = [0,np.pi]
    
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
    phase_bounds_est = [0,np.pi]
    
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
