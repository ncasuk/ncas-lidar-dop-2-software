import numpy as np
from numpy.polynomial import polynomial as P

"""
Quality Control for aerosol-backscatter-radial-winds files for ncas-lidar-dop-2
Based on QC_STARE_v0.m in original matlab version 
  (see release 0.1.0 of the ncasuk ncas-lidar-dop-2-software repo)
  
flags
   1 - data good
   2 - data outside measurment range (greater set distance)
   3 - Signal below instrument threshold
   4 - LoS > |19m\s|
   5 - LoS shear >|5ms-1|
   6 - internal temperature < 15
   7 - intenal temperature > 40
   8 - gate index greater than number of gate measurements in use
   9 - suspect data time error
6 and 7 currently need to be added by hand, not coded for
8 and 9 would likely cause errors in the making of the netcdf file before 
  reaching this point, and so are not coded for at this time
"""

def flag2(ranges, flags, threshold = 9000):
    """
    Flag 2 if range is too big
    """
    flags = np.where(ranges > threshold, 2, flags)
    return flags


def flag3(intensity, backscatter, flags, min_backscatter = 1e-7, max_backscatter = 1e-3):
    """
    Flag 3 if signal below instrument threshold
    """
    for i in range(intensity.shape[0]):  # for each ray
        # part 1
        ix = np.where((intensity[i,:] > 1) & (intensity[i,:] < 1.015))
        threshold = np.mean(intensity[i,ix]) + 1.5 * np.std(intensity[i,ix])
        flags[i] = np.where(intensity[i,:] < threshold, 3, flags[i])
        
        # part 2
        gates = backscatter.shape[1]
        if np.mean(backscatter[i,-21:-1]) > 0:
            ix = np.where(backscatter[i]<0)[0]
            if (gates-2)-(ix[-1]) > 2:
                X = list(range(ix[-1],gates-2))
                Y = np.log10(backscatter[i,ix[-1]:gates-2])
                XX = list(range(ix[-1],gates))
                coeffs = P.polyfit(X,Y,2)
                YY = P.polyval(XX,coeffs)
                Y1 = np.zeros(gates)
                Y1[ix[-1]:] = YY
                tmp_backscat = backscatter[i]
                tmp_flags = flags[i]
                flags[i] = np.where(backscatter[i] < Y1*1.2, 3, flags[i])
            
    # part 3
    flags = np.where(backscatter > max_backscatter, 3, flags)
    flags = np.where(backscatter < min_backscatter, 3, flags)
    return flags


def flag4(velocity, flags, min_thresh = -19, max_thresh = 19):
    """
    Flag 4 if velocity is too big/small
    """
    flags = np.where(velocity > max_thresh, 4, flags)
    flags = np.where(velocity < min_thresh, 4, flags)
    return flags


def flag5(velocity, flags, min_thresh = -5, max_thresh = 5):
    """
    Flag 5 if velocity shear is too big/small
    """
    shear = velocity[:,1:] - velocity[:,:-1]
    flags[:,1:] = np.where(shear > max_thresh, 5, flags[:,1:])
    flags[:,1:] = np.where(shear < min_thresh, 5, flags[:,1:])
    return flags


def make_flags(ranges, velocity, intensity, backscatter):
    # flag 1 for good data - start here, change with bad data
    flags = np.ones_like(ranges)
    for i in range(flags.shape[2]):
        flags[:,:,i] = flag2(ranges[:,:,i], flags[:,:,i])
        flags[:,:,i] = flag3(intensity[:,:,i], backscatter[:,:,i], flags[:,:,i])
        flags[:,:,i] = flag4(velocity[:,:,i], flags[:,:,i])
        flags[:,:,i] = flag5(velocity[:,:,i], flags[:,:,i])
    return flags