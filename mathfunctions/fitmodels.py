import numpy as np
import scipy.signal as spsig
from scipy.ndimage import gaussian_filter1d
import scipy.stats as stats
import matplotlib.pyplot as plt

"""
_prefit functions are called from fitmodelclass.do_prefit(). They are called with sorted array values on the x-axis.
"""

########################  sinewave model
def sinewave_base(fitparams,independent_var):
    """
    fitparams = [frequency, amplitude, phase, verticaloffset]
    """
    return fitparams[1]*np.sin(2*np.pi*fitparams[0]*independent_var + fitparams[2]) + fitparams[3]

def sinewave(fitparams,independent_var,measured_data,errorbars):
    """
    fitparams = [frequency, amplitude, phase, verticaloffset]
    """
    return (sinewave_base(fitparams,independent_var) - measured_data)/errorbars

def sinewave_check(fitparams):
    if len(fitparams) == 4:
        return True
    else:
        return False

def sinewave_paramdict():
    fitparam_dict = {"frequency":None, "amplitude":None, "phase":None, "verticaloffset":None}
    return fitparam_dict

def sinewave_prefit(independent_var, measured_data, errorbars, fitparam_dict, fitparam_bounds_dict, low_pts=5,high_pts=5,num_periods=5) -> bool:
    """
    This requires the x-values, y-values, and the error bars (although error bars are not really necessary 
    but it's just for uniformity, one can simply set them all to 1.

    It also requires fitparam_dict and fitparam_bounds_dict. It will look if any values in fitparam_dict have already been set 
    and use those params, and estimate the other params as well as it can. It will also set the fitparameter bounds so that those can be used in the fitter. 
    """
   
    if not fitparam_dict:
        print("Message from sinewave_prefit: You did not supply a dictionary of parameters to put the prefit into. Prefitting impossible, not returning any dictionaries for fitting and plotting")
        return False

    if not fitparam_bounds_dict:
        print("Message from sinewave_prefit: You did not supply a dictionary of parameter bounds to put the prefit into. Prefitting impossible, not returning any dictionaries for fitting and plotting")
        return False

    # we want to keep the values for start parameters constant if they have been given externally!

    # first we estimate the amplitude
    if fitparam_dict["amplitude"] is None: # this means that it has not been given externally
        low_est = np.mean(np.partition(measured_data,low_pts)[0:low_pts])
        high_est = -1*np.mean(np.partition(-1*measured_data,high_pts)[0:high_pts])
        amplitude_est = 0.5*(high_est-low_est)
        fitparam_dict["amplitude"] = amplitude_est

    if fitparam_bounds_dict["amplitude"] is None: # this means that it has not been given externally
        if fitparam_dict["amplitude"] > 0:
            amplitude_bounds_est = [0,2*fitparam_dict["amplitude"]]
        else:
            amplitude_bounds_est = [2 * fitparam_dict["amplitude"],0]
        fitparam_bounds_dict["amplitude"] = amplitude_bounds_est

    # now we estimate the verticaloffset
    if fitparam_dict["verticaloffset"] is None:
        low_est = np.mean(np.partition(measured_data,low_pts)[0:low_pts])
        high_est = -1*np.mean(np.partition(-1*measured_data,high_pts)[0:high_pts])
        vertical_offset_est = low_est+fitparam_dict["amplitude"]
        fitparam_dict["verticaloffset"] = vertical_offset_est
    if fitparam_bounds_dict["verticaloffset"] is None:
        low_est = np.mean(np.partition(measured_data, low_pts)[0:low_pts])
        high_est = -1 * np.mean(np.partition(-1 * measured_data, high_pts)[0:high_pts])
        vertical_offset_bounds_est = [low_est,high_est]
        fitparam_bounds_dict["verticaloffset"] = vertical_offset_bounds_est

    # now we estimate the phase
    if fitparam_dict["phase"] is None:
        fitparam_dict["phase"] = 1e-5 #this is just effectively 0
    if fitparam_bounds_dict["phase"] is None:
        phase_bounds_est = [-np.pi,np.pi]
        fitparam_bounds_dict["phase"] = phase_bounds_est

    # now we estimate the frequency
    if fitparam_dict["frequency"] is None:
        frequency_est = num_periods/(np.max(independent_var)-np.min(independent_var))
        fitparam_dict["frequency"] = frequency_est
    if fitparam_bounds_dict["frequency"] is None:
        frequency_bounds_est = [0.7*fitparam_dict["frequency"],
                                1.3*fitparam_dict["frequency"]]
        fitparam_bounds_dict["frequency"] = frequency_bounds_est

    return True

# ============= The rest not checked yet

#TODO: Check the other functions
########################### damped sinewave model

def damped_sinewave_base(fitparams,independent_var):
    """
    fitparams = [frequency, amplitude, phase, verticaloffset, dampingconstant]
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

def damped_sinewave_prefit(independent_var,measured_data,errorbars,fitparam_dict,fitparam_bounds_dict,low_pts = 5, high_pts = 5, num_periods = 5) -> bool:

    """
    This requires the x-values, y-values, and the error bars (although error bars are not really necessary 
    but it's just for uniformity, one can simply set them all to 1.

    It also requires fitparam_dict and fitparam_bounds_dict. It will look if any values in fitparam_dict have already been set 
    and use those params, and estimate the other params as well as it can. It will also set the fitparameter bounds so that those can be used in the fitter. 
    """
   
    if not fitparam_dict:
        print("Message from damped_sinewave_prefit: You did not supply a dictionary of parameters to put the prefit into. Prefitting impossible, not returning any dictionaries for fitting and plotting")
        return False

    if not fitparam_bounds_dict:
        print("Message from damped_sinewave_prefit: You did not supply a dictionary of parameter bounds to put the prefit into. Prefitting impossible, not returning any dictionaries for fitting and plotting")
        return False


    # first we estimate the amplitude
    if fitparam_dict["amplitude"]:
        amplitude_est = fitparam_dict["amplitude"]
        amplitude_bounds_est = [0.7*amplitude_est,1.3*amplitude_est]
    else:
        # we take the average of the five highest points and five lowest points, take the difference and divide by 2. 
        #That is the guess of the amplitude
        low_est = np.mean(np.partition(measured_data,low_pts)[0:low_pts])
        high_est = -1*np.mean(np.partition(-1*measured_data,high_pts)[0:high_pts])
        amplitude_est = 0.5*(high_est-low_est)
        amplitude_bounds_est = [0,2*amplitude_est]

    fitparam_dict["amplitude"] = amplitude_est
    if not fitparam_bounds_dict["amplitude"]:
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
    if not fitparam_bounds_dict["verticaloffset"]:
        fitparam_bounds_dict["verticaloffset"] = vertical_offset_bounds_est
    
    # now we estimate the phase
    if fitparam_dict["phase"]:
        phase_est = fitparam_dict["phase"]
    else:
        # set the phase estimate effectively to 0
        phase_est = 1e-5 
    phase_bounds_est = [-np.pi,np.pi]
    
    fitparam_dict["phase"] = phase_est
    if not fitparam_bounds_dict["phase"]:
        fitparam_bounds_dict["phase"] = phase_bounds_est

    # now we estimate the frequency
    if fitparam_dict["frequency"]:
        frequency_est = fitparam_dict["frequency"]
        frequency_bounds_est = [0.7*frequency_est,1.3*frequency_est]
    else:
        # We have to somehow guess the frequency. This is a bit difficult with no data at all, that's why there's that 
        #num_periods parameter at the beginning, which is like, roughly how many periods of the wave do we expect in the 
        #dataset. I just set it at 5 as a wild guess
        frequency_est = num_periods/(np.max(independent_var)-np.min(independent_var))
        frequency_bounds_est = [0.5/(np.max(independent_var)-np.min(independent_var)),
                            0.5*len(independent_var)/(np.max(independent_var)-np.min(independent_var))]
   
    fitparam_dict["frequency"] = frequency_est
    if not fitparam_bounds_dict["frequency"]:
        fitparam_bounds_dict["frequency"] = frequency_bounds_est

    # The automatic estimate is not good yet, I need to find a good way to estimate it
    if fitparam_dict["dampingconstant"]:
        dampingconstant_est = fitparam_dict["dampingconstant"]
        dampingconstant_bounds_est = [0.7*dampingconstant_est,1.3*dampingconstant_est]
    else:
        dampingconstant_est = num_periods/frequency_est
        dampingconstant_bounds_est = [dampingconstant_est - dampingconstant_est/2.,dampingconstant_est + dampingconstant_est/2.]
   
    fitparam_dict["dampingconstant"] = dampingconstant_est
    if not fitparam_bounds_dict["dampingconstant"]:
        fitparam_bounds_dict["dampingconstant"] = dampingconstant_bounds_est
    return True

def gaussian_base(fitparams,independent_var):
    """
    fitparams = [height, center, sigma, verticaloffset]
    defined in the actual normal distribution sense, not like 1/e^2 in optics
    there is NO normalization factor in front, 1/sigma*sqrt(2*pi). Normalization doesn't really matter for us here, and in this manner the height really determines the height of the peak above the baseline. If height = 1, the height of the peak is 1
    """
    return fitparams[0]*np.exp(-0.5*np.power(independent_var - fitparams[1],2.)/np.power(fitparams[2],2.)) + fitparams[3]

def gaussian(fitparams,independent_var,measured_data,errorbars):
    """
    fitparams = [height, center, sigma, verticaloffset]
    """
    return (gaussian_base(fitparams,independent_var) - measured_data)/errorbars

def gaussian_check(fitparams,return_fitparam_empty_dict = False) -> bool:
    if len(fitparams) == 4:
        return True
    else:
        return False

def gaussian_paramdict() -> dict:
    fitparam_dict = {"height":None, "center":None, "sigma":None, "verticaloffset":None}
    return fitparam_dict

# TODO: Write a nice and reliable prefitter for a Gaussian
def gaussian_prefit(independent_var, measured_data, errorbars,
        fitparam_dict, fitparam_bounds_dict, 
        fraction_frontback=0.1,vertoffset_deviation_fraction = 0.3,
        num_periods=5) -> bool:
    """
    This requires the x-values, y-values, and the error bars (although error bars are not really necessary 
    but it's just for uniformity, one can simply set them all to 1.

    It also requires fitparam_dict and fitparam_bounds_dict. It will look if any values in fitparam_dict have already been set 
    and use those params, and estimate the other params as well as it can. It will also set the fitparameter bounds so that those can be used in the fitter. 
    """
   
    if not fitparam_dict:
        print("Message from gaussian_prefit: You did not supply a dictionary of parameters to put the prefit into. Prefitting impossible, not returning any dictionaries for fitting and plotting")
        return False

    if not fitparam_bounds_dict:
        print("Message from gaussian_prefit: You did not supply a dictionary of parameter bounds to put the prefit into. Prefitting impossible, not returning any dictionaries for fitting and plotting")
        return False

    # first we estimate the vertical offset by looking at the average of the data at the edges, which is assumed to be away from the Gaussian peak
    if fitparam_dict["verticaloffset"]:
        vertoffset_est = fitparam_dict["verticaloffset"]
        vertoffset_deviation = np.abs(vertoffset_est * vertoffset_deviation_fraction)
        vertoffset_bounds_est = [vertoffset_est - vertoffset_deviation,
                                 vertoffset_est + vertoffset_deviation]
    else:
        arraylen_fraction = int(len(measured_data)*fraction_frontback)
        vertoffset_est = np.mean(np.union1d(measured_data[0:arraylen_fraction],measured_data[-arraylen_fraction:]))
        vertoffset_deviation = np.abs(vertoffset_est*vertoffset_deviation_fraction)
        vertoffset_bounds_est = [vertoffset_est - vertoffset_deviation,
               vertoffset_est + vertoffset_deviation]

    fitparam_dict["verticaloffset"] = vertoffset_est
    if not fitparam_bounds_dict["verticaloffset"]:
        fitparam_bounds_dict["verticaloffset"] =  vertoffset_bounds_est
    
    data_subtracted_background = measured_data - vertoffset_est
    # now we estimate the position of the center
    if fitparam_dict["center"]:
        center_est = fitparam_dict["center"]
        center_bounds_est = [0.7*center_est,1.3*center_est]
    else:
        # we use the Savitzky-Golay filter from scipy.filter, and then find the 
        #location of the max of the filtered array
        filtered_savgol = spsig.savgol_filter(data_subtracted_background,9,3)
        filtered_savgol_abs = np.abs(filtered_savgol)
        center_est = independent_var[np.argmax(filtered_savgol_abs)]
        center_bounds_est = [0,independent_var[-1]]
    fitparam_dict["center"] = center_est
    if not fitparam_bounds_dict["center"]:
        fitparam_bounds_dict["center"] = center_bounds_est

    
    # now we estimate the height
    #note that the height can be negative, in which case the Gaussian points downwards
    if fitparam_dict["height"]:
        height_est = fitparam_dict["height"]
        height_bounds_est = sorted([0.7*height_est, 1.3*height_est])
    else:
        # basically the height is just the value of the function at the maximum point 
        #(evaluated after smoothing with the Savitzky-Golay filter)
        filtered_savgol = spsig.savgol_filter(data_subtracted_background,9,3)
        index_of_center = np.argmin(np.abs(independent_var - center_est))
        height_est = filtered_savgol[index_of_center]
        height_bounds_est = sorted([height_est - 0.3*height_est, height_est + 0.3*height_est])
    fitparam_dict["height"] = height_est
    if not fitparam_bounds_dict["height"]:
        fitparam_bounds_dict["height"] = height_bounds_est
    

    # now we estimate the frequency
    if fitparam_dict["sigma"]:
        sigma_est = fitparam_dict["sigma"]
        sigma_bounds_est = sorted([sigma_est / 3., 3 * sigma_est])
    else:
        # we do the max likelihood estimation of the sigma
        sum_squared_differences = np.sum(np.power(data_subtracted_background - center_est,2.))
        sigma_est = 0.25*np.sqrt(sum_squared_differences/len(data_subtracted_background))
        # NOTE!!! That factor of 0.25 is kind of arbitrary
        sigma_bounds_est = sorted([sigma_est/3.,3*sigma_est])
    fitparam_dict["sigma"] = sigma_est
    if not fitparam_bounds_dict["sigma"]:
        fitparam_bounds_dict["sigma"] = sigma_bounds_est

    return True
#===============================================

# Section for fitting a line
def linearfit_base(fitparams,independent_var):
    """
    fitparams = [slope,yintercept]
    """
    return fitparams[0]*independent_var + fitparams[1]

def linearfit(fitparams,independent_var,measured_data,errorbars):
    """
    fitparams = [slope,yintercept]
    """
    return (linearfit_base(fitparams,independent_var) - measured_data)/errorbars

def linearfit_check(fitparams):
    if len(fitparams) == 2:
        return True
    else:
        return False

def linearfit_paramdict() -> dict:
    fitparam_dict = {"slope":None, "yintercept":None}
    return fitparam_dict

def linearfit_prefit(independent_var, measured_data, errorbars, fitparam_dict, fitparam_bounds_dict) -> bool:
    """
    This requires the x-values, y-values, and the error bars (although error bars are not really necessary 
    but it's just for uniformity, one can simply set them all to 1.

    It also requires fitparam_dict and fitparam_bounds_dict. It will look if any values in fitparam_dict have already been set 
    and use those params, and estimate the other params as well as it can. It will also set the fitparameter bounds so that those can be used in the fitter. 
    """
   
    if not fitparam_dict:
        print("Message from linearfit_prefit: You did not supply a dictionary of parameters to put the prefit into. Prefitting impossible, not returning any dictionaries for fitting and plotting")
        return False

    if not fitparam_bounds_dict:
        print("Message from linearfit_prefit: You did not supply a dictionary of parameter bounds to put the prefit into. Prefitting impossible, not returning any dictionaries for fitting and plotting")
        return False

    # we want to keep the values for start parameters constant if they have been given externally!

    # first we estimate the slope
    if fitparam_dict["slope"] is None: # this means that it has not been given externally
        
        xval_indices = np.random.choice(list(range(len(independent_var))),np.maximum(2,int(len(independent_var)/3.)),replace=False)
        xval_indices_sorted = np.sort(xval_indices)
        xval_samples = independent_var[xval_indices_sorted] # I just recast it here so that it's sorted
        yval_samples = measured_data[xval_indices_sorted]
        yval_diffs = np.diff(yval_samples) # this is a sample of "rises"
        xval_diffs = np.diff(xval_samples) # this is the corresponding sample of "runs"
        slope_est = np.mean(yval_diffs/xval_diffs)
        fitparam_dict["slope"] = slope_est

    if fitparam_bounds_dict["slope"] is None: # this means that it has not been given externally
        slope_bounds_est = [-1e100,1e100]
        fitparam_bounds_dict["slope"] = slope_bounds_est

    # now we estimate the yintercept
    if fitparam_dict["yintercept"] is None:
        xval_indices = np.random.choice(list(range(len(independent_var))),np.maximum(2,int(len(independent_var)/3.)),replace=False)
        xval_indices_sorted = np.sort(xval_indices)
        xval_samples = independent_var[xval_indices_sorted] # I just recast it here so that it's sorted
        yval_samples = measured_data[xval_indices_sorted]
        yintercept_estimates = yval_samples - fitparam_dict["slope"]*xval_samples
        yintercept_est = np.mean(yintercept_estimates)
        fitparam_dict["yintercept"] = yintercept_est

    if fitparam_bounds_dict["yintercept"] is None:
        yintercept_bounds_est = [-1e100,1e100]
        fitparam_bounds_dict["yintercept"] = yintercept_bounds_est

    return True

# Section for fitting a line
def parabolicfit_base(fitparams,independent_var):
    """
    fitparams = [aparam,bparam,cparam]
    """
    return fitparams[0]*np.power(independent_var,2.) + fitparams[1]*independent_var + fitparams[2]

def parabolicfit(fitparams,independent_var,measured_data,errorbars):
    """
    fitparams = [aparam,bparam,cparam]
    """
    return (parabolicfit_base(fitparams,independent_var) - measured_data)/errorbars

def parabolicfit_check(fitparams):
    if len(fitparams) == 3:
        return True
    else:
        return False

def parabolicfit_paramdict() -> dict:
    fitparam_dict = {"aparam":None, "bparam":None, "cparam":None}
    return fitparam_dict

def parabolicfit_prefit(independent_var, measured_data, errorbars, fitparam_dict, fitparam_bounds_dict) -> bool:
    """
    This requires the x-values, y-values, and the error bars (although error bars are not really necessary 
    but it's just for uniformity, one can simply set them all to 1.

    It also requires fitparam_dict and fitparam_bounds_dict. It will look if any values in fitparam_dict have already been set 
    and use those params, and estimate the other params as well as it can. It will also set the fitparameter bounds so that those can be used in the fitter. 

    NOTE: It's not the best prefitter yet, but it seems to work for reasonable parabolas. 
    The automatic initial parameter estimation routines can of course be improved, for the cases 
    where there is a lot of noise in the data

    """
   
    if not fitparam_dict:
        print("Message from linearfit_prefit: You did not supply a dictionary of parameters to put the prefit into. Prefitting impossible, not returning any dictionaries for fitting and plotting")
        return False

    if not fitparam_bounds_dict:
        print("Message from linearfit_prefit: You did not supply a dictionary of parameter bounds to put the prefit into. Prefitting impossible, not returning any dictionaries for fitting and plotting")
        return False

    # we want to keep the values for start parameters constant if they have been given externally!

    # first we estimate the aparam
    if fitparam_dict["aparam"] is None: # this means that it has not been given externally
        # get the average distance between the points and smooth using a Gaussian filter
        avg_distance_xpoints = (independent_var[-1] - independent_var[0])/len(independent_var)
        gauss_smoothing_width = 5*avg_distance_xpoints # width of the Gaussian kernel is 5

        smoothed_data = gaussian_filter1d(measured_data,gauss_smoothing_width)
        firstderivative = np.gradient(smoothed_data,independent_var)
        secondderivative = np.gradient(firstderivative,independent_var)

        # Now calculate the z-score for all numbers and discard those that are more than 1 st dev away
        secondderivative_zcondition = np.abs(stats.zscore(secondderivative)) <= 1. 
        aparam_est = np.mean(secondderivative[secondderivative_zcondition])/2.
        fitparam_dict["aparam"] = aparam_est

    if fitparam_bounds_dict["aparam"] is None: # this means that it has not been given externally
        
        aparam_bounds_est = [-1e100,1e100]
        fitparam_bounds_dict["aparam"] = aparam_bounds_est

    # now we estimate the bparam
    if fitparam_dict["bparam"] is None:
        firstderivative = np.gradient(measured_data,independent_var)
        b_estimates = firstderivative - 2*fitparam_dict["aparam"]*independent_var
        bparam_est = np.mean(b_estimates)
        #TODELETE:
        print("bparam_est: ",bparam_est)
        fitparam_dict["bparam"] = bparam_est

    if fitparam_bounds_dict["bparam"] is None:
        bparam_bounds_est = [-1e100,1e100]
        fitparam_bounds_dict["bparam"] = bparam_bounds_est
    
    if fitparam_dict["cparam"] is None:
        c_estimates = measured_data - np.power(independent_var,2.)*fitparam_dict["aparam"] - independent_var*fitparam_dict["bparam"]
        cparam_est = np.mean(c_estimates)
        #TODELETE:
        print("cparam_est: ",cparam_est)
        fitparam_dict["cparam"] = cparam_est

    if fitparam_bounds_dict["cparam"] is None: 
        cparam_bounds = [-1e100,1e100]
        fitparam_bounds_dict["cparam"] = cparam_bounds 

    return True
########################  RAP shelving, maximizing difference between two curves
# we can feed already the difference itself as a single dataset
def curvepeak_base(fitparams,independent_var):
    """
    """
    return None

def curvepeak(fitparams,independent_var,measured_data,errorbars):
    """
    """
    return None

def curvepeak_check(fitparams):
    if len(fitparams) == 4:
        return True
    else:
        return False

def curvepeak_paramdict():
    fitparam_dict = {"peakcoordinate":None,"peakvalue":None,"numpeaks":None,"smoothing":None, "inversion":None}
    return fitparam_dict

def curvepeak_prefit(independent_var, measured_data, errorbars, fitparam_dict, fitparam_bounds_dict) -> bool:
    """
    This requires the x-values, y-values, and the error bars (although error bars are not really necessary 
    but it's just for uniformity, one can simply set them all to 1.

    It also requires fitparam_dict and fitparam_bounds_dict. It will look if any values in fitparam_dict have already been set 
    and use those params, and estimate the other params as well as it can. It will also set the fitparameter bounds so that those can be used in the fitter. 
    """
   
    if not fitparam_dict:
        print("Message from sinewave_prefit: You did not supply a dictionary of parameters to put the prefit into. Prefitting impossible, not returning any dictionaries for fitting and plotting")
        return False

    if not fitparam_bounds_dict:
        print("Message from sinewave_prefit: You did not supply a dictionary of parameter bounds to put the prefit into. Prefitting impossible, not returning any dictionaries for fitting and plotting")
        return False

    # if we set the inversion parameter to 1, that means that we will invert the inputs
    # otherwise we ignore whatever is there and do no inversion
    if fitparam_dict["inversion"] == 1:
        measured_data = -1*measured_data ##

    if isinstance(fitparam_dict["smoothing"],(int,float)): # this means that it has not been given externally
        if fitparam_dict["smoothing"] <= 0: 
            print("Message from curvepeak_prefit: you gave an input for Gaussian smoothing that is less than or equal 0. This is not allowed. Not doing any Gaussian smoothing on the data")
        else: # we apply a Gaussian smoothing filter to the data
            measured_data = gaussian_filter1d(measured_data,fitparam_dict["smoothing"])
    
    if fitparam_dict["numpeaks"] is None:
        fitparam_dict["numpeaks"] = 1
    elif isinstance(fitparam_dict["numpeaks"],int):
        if fitparam_dict["numpeaks"] < 1:
            print("Message from curvepeak_prefit: numpeaks requested must be an integer greater or equal to 1. Setting numpeaks = 1")
            fitparam_dict["numpeaks"] = 1
    else:
        print("Message from curvepeak_prefit: numpeaks requested must be an integer, and now it is apparently not. Setting numpeaks = 1")
        fitparam_dict["numpeaks"] = 1
    
    # since this is not really a fit, we don't have any bounds
    # just to keep interface consistens, we set all bounds that are None 
    # to [0,1]
    for (key,value) in fitparam_bounds_dict.items():
        if value is None: 
            fitparam_bounds_dict[key] = [0,1]

    return True

