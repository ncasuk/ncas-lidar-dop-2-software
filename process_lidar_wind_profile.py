import datetime as dt
import numpy as np
from netCDF4 import Dataset
import csv
from bisect import bisect_left

import read_lidar
import aerosol_backscatter_qc
from ncas_amof_netcdf_template import create_netcdf, util, remove_empty_variables



def uv_from_dir(u,v):
    """
    Given u and v wind speeds, returns direction wind travelling from
    """
    if v == 0:
        if u >= 0:
            a = 270
        else:
            a = 90
    else:
        a = np.rad2deg(np.arctan(u/v))
        if v > 0:
            a += 180
        if v < 0:
            if u > 0:
                a += 360
    return (a)



def find_closest(numberlist, number, which='closest'):
    """
    Given a list and a desired number, this function finds the closest number
    in the list to the desired number. If two numbers in the list are equally
    close, the smaller one is returned.
    Options:
    which
         'closest' - returns number and index of number closest in list.
                     Default option.
         'lower'   - returns number and index of number in list immediately
                     below given number.
         'higher'  - returns number and index of number in list immediately
                     above given number.
         'both'    - returns number and index of number above and below it in
                     list.
    Returns number in list and index of that number in list.
    """
    if which not in {'closest', 'lower', 'higher', 'both'}:
        msg = "Invalid option for which - valid options are 'closest', 'lower', 'higher', and 'both'"
        raise ValueError(msg)
    pos = bisect_left(numberlist, number)
    if not isinstance(numberlist,list):
        numberlist=list(numberlist)
    if pos == 0:
        return numberlist[0],0
    if pos == len(numberlist):
        return numberlist[-1],numberlist.index(numberlist[-1])
    before=numberlist[pos-1]
    after=numberlist[pos]
    if which == 'closest':
        if after-number < number-before:
            return after, numberlist.index(after)
        else:
            return before, numberlist.index(before)
    elif which == 'lower':
        return before, numberlist.index(before)
    elif which == 'higher':
        return after, numberlist.index(after)
    elif which == 'both':
        return before, after, numberlist.index(before), numberlist.index(after)


    
def get_data(lidar_file):
    data = read_lidar.readLidarFile(lidar_file)
    
    # need to create 3d arrays with dimensions time, index_of_range, index_of_angle
    # how many angles are there? (hopefully only 1, that's all I've written this for at the moment
    el_rounded = set([round(i,1) for i in set(data['EL'][:,0])])
    az_rounded = set([round(i,1) for i in set(data['AZ'][:,0])])
    no_angles = len(az_rounded)
    
    datarange = np.ma.ones((1, data['gate_number'], no_angles)) * -9999
    datarange = np.ma.masked_where(datarange == -9999, datarange)
    datarange[0,:,:] = data['A'].T
    
    datavel = np.ma.ones((1, data['gate_number'], no_angles)) * -9999
    datavel = np.ma.masked_where(datavel == -9999, datavel)
    datavel[0,:,:] = data['D'].T
    
    databs = np.ma.ones((1, data['gate_number'], no_angles)) * -9999
    databs = np.ma.masked_where(databs == -9999, databs)
    databs[0,:,:] = data['B'].T
    
    dataint = np.ma.ones((1, data['gate_number'], no_angles)) * -9999
    dataint = np.ma.masked_where(dataint == -9999, dataint)
    dataint[0,:,:] = data['I'].T
    
    return data, no_angles, datarange, datavel, databs, dataint



def calculate_3d_winds(data):
    altitudes = (data['A'][:,:] * np.sin(np.deg2rad(data['EL'][:])))
    # index of vertical pointing beam. Well, first find biggest elevation, check it's 90 (or close to, e.g. 90.01 is okay)
    for i in np.where((data['EL'])==(np.max(data['EL'])))[0]:
        if abs(data['EL'][i] - 90) < 0.5:  # np.sin(89.5) = 0.9996, 9585 * 0.9996 = 9584.64. I'd say +/- 0.5 deg is okay
            vertical_beam = i
            vertical_coords = data['A'][i]
    # find indexs for 90 and 0/360 azimuths
    for i in range(len(data['AZ'])):
        if abs(data['AZ'][i]-90) < 0.5:
            az90_index = i
        elif abs(data['AZ'][i]-360) < 0.5 or abs(data['AZ'][i]-0) < 0.5:
            az360_index = i
    # find max height to use, this will be minimum highest height from the three beams
    max_height = np.min(altitudes[:,-1])  # 4795.5 in this example
    # now only want vertical coords that are less than max_height
    vertical_coords = vertical_coords[np.where(vertical_coords <= max_height)]
    # find closest gate in each beam to the vertical coords
    indexs_beam0 = []  # vertical
    indexs_beam1 = []  # 0/360
    indexs_beam2 = []  # 90
    for v in vertical_coords:
        indexs_beam0.append(find_closest(altitudes[vertical_beam], v)[1])
        indexs_beam1.append(find_closest(altitudes[az360_index], v)[1])
        indexs_beam2.append(find_closest(altitudes[az90_index], v)[1])
        
    all_vr1s = data['D'][vertical_beam, indexs_beam0]
    all_vr2s = data['D'][az90_index, indexs_beam2]
    all_vr3s = data['D'][az360_index, indexs_beam1]  
    dop_winds = np.array([all_vr1s,all_vr2s,all_vr3s])
    
    angle_array = np.array([[np.tan(np.deg2rad(data['EL'][az90_index,0])), -1/np.cos(np.deg2rad(data['EL'][az90_index,0])), 0],
                            [np.tan(np.deg2rad(data['EL'][az360_index,0])), 0,                                             -1/np.cos(np.deg2rad(data['EL'][az360_index,0]))],
                            [-1,                                            0,                                              0]])
    # Matrix multiplication
    threedwinds = angle_array@dop_winds
    
    wind_speed = (threedwinds[0,:]**2 + threedwinds[1,:]**2) ** 0.5  # 2D wind speed
    wdir = np.empty(threedwinds[0].shape)
    for i in range(threedwinds[0].shape[0]):
        wdir[i] = uv_from_dir(threedwinds[0,i],threedwinds[1,i])
        
    return vertical_coords, threedwinds, wind_speed, wdir
    



def make_netcdf_aerosol_backscatter_radial_winds(lidar_files, metadata_file = None, ncfile_location = '.', verbose = False):
    """
    lidar_files - list
    """
    all_data = {}
    for i in range(len(lidar_files)):
        if verbose:
            print(f'Reading file {i+1} of {len(lidar_files)}')
        if i == 0:
            data, no_angles, datarange, datavel, databs, dataint = get_data(lidar_files[i])
            all_data[str(i)] = data 
            
            unix_times, doy, years, months, days, hours, minutes, seconds, time_coverage_start_dt, time_coverage_end_dt, file_date = util.get_times(data['DP'])
            time_coverage_start_dt = [time_coverage_start_dt]
            time_coverage_end_dt = [time_coverage_end_dt]
            file_date = [file_date]
            
        else:
            this_data, this_no_angles, this_datarange, this_datavel, this_databs, this_dataint = get_data(lidar_files[i])
            all_data[str(i)] = this_data
            no_angles = np.vstack((no_angles,this_no_angles))
            datarange = np.vstack((datarange,this_datarange))
            datavel = np.vstack((datavel,this_datavel))
            databs = np.vstack((databs,this_databs))
            dataint = np.vstack((dataint,this_dataint))
            
            this_unix_times, this_doy, this_years, this_months, this_days, this_hours, this_minutes, this_seconds, this_time_coverage_start_dt, this_time_coverage_end_dt, this_file_date = util.get_times(this_data['DP'])
            
            unix_times.extend(this_unix_times)
            doy.extend(this_doy)
            years.extend(this_years)
            months.extend(this_months)
            days.extend(this_days)
            hours.extend(this_hours)
            minutes.extend(this_minutes)
            seconds.extend(this_seconds)
            time_coverage_start_dt.append(this_time_coverage_start_dt)
            time_coverage_end_dt.append(this_time_coverage_end_dt)
            file_date.append(this_file_date)
            
    if verbose: print('Doing QC')
    flags = aerosol_backscatter_qc.make_flags(datarange, datavel, dataint, databs)
            
            
    actual_no_angles = no_angles[0][0]
    
    inst_azimuths = np.ma.ones((len(unix_times[::actual_no_angles]),3)) * -9999
    inst_azimuths = np.ma.masked_where(inst_azimuths == -9999, inst_azimuths)
    
    inst_elevations = np.ma.ones((len(unix_times[::actual_no_angles]),3)) * -9999
    inst_elevations = np.ma.masked_where(inst_elevations == -9999, inst_elevations)
    
    for key, value in all_data.items():
        inst_azimuths[int(key)] = value['AZ'][:,0]
        inst_elevations[int(key)] = value['EL'][:,0]
    
    if verbose:
        print('Making netCDF file')
    create_netcdf.main('ncas-lidar-dop-2', date = file_date[0], dimension_lengths = {'time':len(unix_times)/actual_no_angles, 'index_of_range': all_data['0']['gate_number'], 'index_of_angle': actual_no_angles}, loc = 'land', products = ['aerosol-backscatter-radial-winds'], file_location = ncfile_location, options='wind-profile')
    ncfile = Dataset(f'{ncfile_location}/ncas-lidar-dop-2_iao_{file_date[0]}_aerosol-backscatter-radial-winds_wind-profile_v1.0.nc', 'a')
    
    # needed due to error in AMOF google sheets
    ncfile.createVariable('qc_flag_radial_velocity_of_scatterers_away_from_instrument', 'b', dimensions=('time', 'index_of_range', 'index_of_angle'))
    ncfile.createVariable('qc_flag_backscatter', 'b', dimensions=('time', 'index_of_range', 'index_of_angle'))
    
    if verbose:
        print('Updating variables')
    util.update_variable(ncfile, 'range', datarange)
    util.update_variable(ncfile, 'radial_velocity_of_scatterers_away_from_instrument', datavel)
    util.update_variable(ncfile, 'attenuated_aerosol_backscatter_coefficient', databs)
    util.update_variable(ncfile, 'signal_to_noise_ratio_plus_1', dataint)
    util.update_variable(ncfile, 'sensor_azimuth_angle_instrument_frame', inst_azimuths)
    util.update_variable(ncfile, 'sensor_view_angle_instrument_frame', inst_elevations)
    util.update_variable(ncfile, 'qc_flag_radial_velocity_of_scatterers_away_from_instrument', flags)
    util.update_variable(ncfile, 'qc_flag_backscatter', flags)
    #util.update_variable(ncfile, 'sensor_azimuth_angle_earth_frame', .....)
    #util.update_variable(ncfile, 'sensor_view_angle_earth_frame', .....)
    util.update_variable(ncfile, 'time', unix_times[::actual_no_angles])
    util.update_variable(ncfile, 'year', years[::actual_no_angles])
    util.update_variable(ncfile, 'month', months[::actual_no_angles])
    util.update_variable(ncfile, 'day', days[::actual_no_angles])
    util.update_variable(ncfile, 'hour', hours[::actual_no_angles])
    util.update_variable(ncfile, 'minute', minutes[::actual_no_angles])
    util.update_variable(ncfile, 'second', seconds[::actual_no_angles])
    util.update_variable(ncfile, 'day_of_year', doy[::actual_no_angles])
    
    ncfile.setncattr('time_coverage_start', dt.datetime.fromtimestamp(min(time_coverage_start_dt), dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S %Z"))
    ncfile.setncattr('time_coverage_end', dt.datetime.fromtimestamp(max(time_coverage_end_dt), dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S %Z"))
    ncfile.setncattr('pulses_per_ray', int(all_data['0']['pulses_per_ray']))
    ncfile.setncattr('rays_per_point', int(all_data['0']['rays_per_point']))
    ncfile.setncattr('focus', f"{int(all_data['0']['focus_range'])}m" if int(all_data['0']['focus_range']) != 65535 else 'Inf')
    ncfile.setncattr('velocity_resolution', f"{float(all_data['0']['resolution'])} m/s")
    ncfile.setncattr('number_of_gates', int(all_data['0']['gate_number']))
    ncfile.setncattr('gate_length', f"{int(all_data['0']['gate_length'])}m")
    
    util.add_metadata_to_netcdf(ncfile, metadata_file)
                
    # if lat and lon given, no need to also give geospatial_bounds
    # this works great for point deployment (e.g. ceilometer)
    lat_masked = ncfile.variables['latitude'][0].mask
    lon_masked = ncfile.variables['longitude'][0].mask
    geospatial_attr_changed = "CHANGE" in ncfile.getncattr('geospatial_bounds')
    if geospatial_attr_changed and not lat_masked and not lon_masked:
        geobounds = f"{ncfile.variables['latitude'][0]}N, {ncfile.variables['longitude'][0]}E"
        ncfile.setncattr('geospatial_bounds', geobounds)
    
    ncfile.close()
    
    if verbose:
        print('Removing empty variables')
    remove_empty_variables.main(f'{ncfile_location}/ncas-lidar-dop-2_iao_{file_date[0]}_aerosol-backscatter-radial-winds_wind-profile_v1.0.nc', verbose = verbose, skip_check = True)


    
def make_netcdf_mean_winds_profile(lidar_files, metadata_file = None, ncfile_location = '.', verbose = False):
    """
    lidar_files - list
    """
    all_data = {}
    for i in range(len(lidar_files)):
        if verbose:
            print(f'Reading file {i+1} of {len(lidar_files)}')
        if i == 0:
            #data, no_angles, datarange, datavel, databs, dataint = get_data(lidar_files[i])
            data, no_angles, *_ = get_data(lidar_files[i])
            all_data[str(i)] = data 
            
            unix_times, doy, years, months, days, hours, minutes, seconds, time_coverage_start_dt, time_coverage_end_dt, file_date = util.get_times(data['DP'])
            time_coverage_start_dt = [time_coverage_start_dt]
            time_coverage_end_dt = [time_coverage_end_dt]
            file_date = [file_date]
            
            altitudes, threedwinds, wind_speed, wdir = calculate_3d_winds(data)
            all_threedwinds = np.empty([len(lidar_files),np.shape(threedwinds)[0],np.shape(threedwinds)[1]])
            all_threedwinds[i] = threedwinds
            all_wind_speed = np.empty([len(lidar_files),np.shape(wind_speed)[0]])
            all_wind_speed[i] = wind_speed
            all_wdir = np.empty([len(lidar_files),np.shape(wdir)[0]])
            all_wdir[i] = wdir

            
        else:
            #this_data, this_no_angles, this_datarange, this_datavel, this_databs, this_dataint = get_data(lidar_files[i])
            this_data, *_ = get_data(lidar_files[i])
            all_data[str(i)] = this_data
            
            this_unix_times, this_doy, this_years, this_months, this_days, this_hours, this_minutes, this_seconds, this_time_coverage_start_dt, this_time_coverage_end_dt, this_file_date = util.get_times(this_data['DP'])
            
            unix_times.extend(this_unix_times)
            doy.extend(this_doy)
            years.extend(this_years)
            months.extend(this_months)
            days.extend(this_days)
            hours.extend(this_hours)
            minutes.extend(this_minutes)
            seconds.extend(this_seconds)
            time_coverage_start_dt.append(this_time_coverage_start_dt)
            time_coverage_end_dt.append(this_time_coverage_end_dt)
            file_date.append(this_file_date)
            
            this_altitudes, this_threedwinds, this_wind_speed, this_wdir = calculate_3d_winds(this_data)
            
            # altitudes should match, if not throw error and stop
            if (this_altitudes != altitudes).any():
                msg = "ERROR: Change in altitudes with time"
                raise ValueError(msg)
                
            all_threedwinds[i] = this_threedwinds
            all_wind_speed[i] = this_wind_speed
            all_wdir[i] = this_wdir
            

    eastward_winds = all_threedwinds[:,0,:]
    northward_winds = all_threedwinds[:,1,:]
    upward_winds = all_threedwinds[:,2,:]
        
    if verbose: 
        print('Making netCDF file')
    create_netcdf.main('ncas-lidar-dop-2', date = file_date[0], dimension_lengths = {'time':len(lidar_files), 'altitude': np.shape(altitudes)[0]}, loc = 'land', products = ['mean-winds-profile'], file_location = ncfile_location)
    ncfile = Dataset(f'{ncfile_location}/ncas-lidar-dop-2_iao_{file_date[0]}_mean-winds-profile_v1.0.nc', 'a')
    
    if verbose:
        print('Updating variables')
    util.update_variable(ncfile, 'altitude', altitudes)
    util.update_variable(ncfile, 'eastward_wind', eastward_winds)
    util.update_variable(ncfile, 'northward_wind', northward_winds)
    util.update_variable(ncfile, 'upward_air_velocity', upward_winds)
    util.update_variable(ncfile, 'wind_speed', all_wind_speed)
    util.update_variable(ncfile, 'wind_from_direction', all_wdir)
    util.update_variable(ncfile, 'time', unix_times[::no_angles])
    util.update_variable(ncfile, 'year', years[::no_angles])
    util.update_variable(ncfile, 'month', months[::no_angles])
    util.update_variable(ncfile, 'day', days[::no_angles])
    util.update_variable(ncfile, 'hour', hours[::no_angles])
    util.update_variable(ncfile, 'minute', minutes[::no_angles])
    util.update_variable(ncfile, 'second', seconds[::no_angles])
    util.update_variable(ncfile, 'day_of_year', doy[::no_angles])
    
    ncfile.setncattr('time_coverage_start', dt.datetime.fromtimestamp(min(time_coverage_start_dt), dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S %Z"))
    ncfile.setncattr('time_coverage_end', dt.datetime.fromtimestamp(max(time_coverage_end_dt), dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S %Z"))
    
    util.add_metadata_to_netcdf(ncfile, metadata_file)
                
    # if lat and lon given, no need to also give geospatial_bounds
    # this works great for point deployment (e.g. ceilometer)
    lat_masked = ncfile.variables['latitude'][0].mask
    lon_masked = ncfile.variables['longitude'][0].mask
    geospatial_attr_changed = "CHANGE" in ncfile.getncattr('geospatial_bounds')
    if geospatial_attr_changed and not lat_masked and not lon_masked:
        geobounds = f"{ncfile.variables['latitude'][0]}N, {ncfile.variables['longitude'][0]}E"
        ncfile.setncattr('geospatial_bounds', geobounds)
    
    ncfile.close()
    
    if verbose:
        print('Removing empty variables')
    remove_empty_variables.main(f'{ncfile_location}/ncas-lidar-dop-2_iao_{file_date[0]}_mean-winds-profile_v1.0.nc', verbose = verbose, skip_check = True)
            
        
    
    
    
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description = 'Create AMOF-compliant netCDF file for ncas-lidar-dop-2 instrument for WIND PROFILE measurements.')
    parser.add_argument('input_file', nargs='*', help = 'Raw lidar data from instrument.')
    parser.add_argument('-v','--verbose', action='store_true', help = 'Print out additional information.', dest = 'verbose')
    parser.add_argument('-m','--metadata', type = str, help = 'csv file with global attributes and additional metadata. Default is None', dest='metadata')
    parser.add_argument('-o','--ncfile-location', type=str, help = 'Path for where to save netCDF file. Default is .', default = '.', dest="ncfile_location")
    parser.add_argument('-p','--products', nargs = '*', help = 'Products of ncas-lidar-dop-2 to make netCDF files for. Options are mean-winds-profile (not yet implemented), aerosol-backscatter-radial-winds, depolarisation-ratio (not yet implemented). One or many can be given (space separated), default is "aerosol-backscatter-radial-winds".', default = ['aerosol-backscatter-radial-winds','mean-winds-profile'])
    args = parser.parse_args()
    
    
    for prod in args.products:
        if prod == 'aerosol-backscatter-radial-winds':
            make_netcdf_aerosol_backscatter_radial_winds(args.input_file, metadata_file = args.metadata, ncfile_location = args.ncfile_location, verbose = args.verbose)
        elif prod == 'mean-winds-profile':
            make_netcdf_mean_winds_profile(args.input_file, metadata_file = args.metadata, ncfile_location = args.ncfile_location, verbose = args.verbose)
        elif prod in ['depolarisation-ratio']:
            print(f'WARNING: {prod} is not yet implemented, continuing with other prodcuts...')
        else:
            print(f'WARNING: {prod} is not recognised for this instrument, continuing with other prodcuts...')
