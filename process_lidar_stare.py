import datetime as dt
import numpy as np
from netCDF4 import Dataset
import csv

import read_lidar
import aerosol_backscatter_qc
from ncas_amof_netcdf_template import create_netcdf, util, remove_empty_variables


    
def get_data(lidar_file):
    data = read_lidar.readLidarFile(lidar_file)
    
    # need to create 3d arrays with dimensions time, index_of_range, index_of_angle
    # how many angles are there? (hopefully only 1, that's all I've written this for at the moment
    el_rounded = set([round(i,1) for i in set(data['EL'][:,0])])
    az_rounded = set([round(i,1) for i in set(data['AZ'][:,0])])
    no_angles = len(el_rounded) * len(az_rounded)
    
    if no_angles != 1:
        print(f"WARNING: More than one elevation/azimuth angle ({no_angles}), code isn't designed to cope with this...")
        print(f"Azimuths: {set(data['AZ'][:,0])}")
        print(f"Elevations: {set(data['EL'][:,0])}")
    
    datarange = np.ma.ones((len(data['TimeStamp']), data['gate_number'], no_angles)) * -9999
    datarange = np.ma.masked_where(datarange == -9999, datarange)
    datarange[:,:,0] = data['A']
    
    datavel = np.ma.ones((len(data['TimeStamp']), data['gate_number'], no_angles)) * -9999
    datavel = np.ma.masked_where(datavel == -9999, datavel)
    datavel[:,:,0] = data['D']
    
    databs = np.ma.ones((len(data['TimeStamp']), data['gate_number'], no_angles)) * -9999
    databs = np.ma.masked_where(databs == -9999, databs)
    databs[:,:,0] = data['B']
    
    dataint = np.ma.ones((len(data['TimeStamp']), data['gate_number'], no_angles)) * -9999
    dataint = np.ma.masked_where(dataint == -9999, dataint)
    dataint[:,:,0] = data['I']
    
    return data, no_angles, datarange, datavel, databs, dataint



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
            
    inst_azimuths = np.ma.ones((len(unix_times),1)) * -9999
    inst_azimuths = np.ma.masked_where(inst_azimuths == -9999, inst_azimuths)
    
    inst_elevations = np.ma.ones((len(unix_times),1)) * -9999
    inst_elevations = np.ma.masked_where(inst_elevations == -9999, inst_elevations)
    
    current_time = 0
    for key, value in all_data.items():
        last_time = current_time + len(value['AZ'][:,0])
        inst_azimuths[current_time:last_time,0] = [round(i,1) for i in value['AZ'][:,0]]#value['AZ'][:,0]
        inst_elevations[current_time:last_time,0] = [round(i,1) for i in value['EL'][:,0]]#value['EL'][:,0]
        current_time = last_time
        
    
    if verbose:
        print('Making netCDF file')
    create_netcdf.main('ncas-lidar-dop-2', date = file_date[0], dimension_lengths = {'time':len(unix_times), 'index_of_range': all_data['0']['gate_number'], 'index_of_angle': no_angles[0]}, loc = 'land', products = ['aerosol-backscatter-radial-winds'], file_location = ncfile_location, options='stare')
    ncfile = Dataset(f'{ncfile_location}/ncas-lidar-dop-2_iao_{file_date[0]}_aerosol-backscatter-radial-winds_stare_v1.0.nc', 'a')
    
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
    util.update_variable(ncfile, 'time', unix_times)
    util.update_variable(ncfile, 'year', years)
    util.update_variable(ncfile, 'month', months)
    util.update_variable(ncfile, 'day', days)
    util.update_variable(ncfile, 'hour', hours)
    util.update_variable(ncfile, 'minute', minutes)
    util.update_variable(ncfile, 'second', seconds)
    util.update_variable(ncfile, 'day_of_year', doy)
    
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
    remove_empty_variables.main(f'{ncfile_location}/ncas-lidar-dop-2_iao_{file_date[0]}_aerosol-backscatter-radial-winds_stare_v1.0.nc', verbose = verbose, skip_check = True)


    
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description = 'Create AMOF-compliant netCDF file for ncas-lidar-dop-2 instrument.')
    parser.add_argument('input_file', nargs='*', help = 'Raw lidar data from instrument.')
    parser.add_argument('-v','--verbose', action='store_true', help = 'Print out additional information.', dest = 'verbose')
    parser.add_argument('-m','--metadata', type = str, help = 'csv file with global attributes and additional metadata. Default is None', dest='metadata')
    parser.add_argument('-o','--ncfile-location', type=str, help = 'Path for where to save netCDF file. Default is .', default = '.', dest="ncfile_location")
    parser.add_argument('-p','--products', nargs = '*', help = 'Products of ncas-lidar-dop-2 to make netCDF files for. Options are mean-winds-profile (not yet implemented), aerosol-backscatter-radial-winds, depolarisation-ratio (not yet implemented). One or many can be given (space separated), default is "aerosol-backscatter-radial-winds".', default = ['aerosol-backscatter-radial-winds'])
    args = parser.parse_args()
    
    
    for prod in args.products:
        if prod == 'aerosol-backscatter-radial-winds':
            make_netcdf_aerosol_backscatter_radial_winds(args.input_file, metadata_file = args.metadata, ncfile_location = args.ncfile_location, verbose = args.verbose)
        elif prod in ['mean-winds-profile', 'depolarisation-ratio']:
            print(f'WARNING: {prod} is not yet implemented, continuing with other prodcuts...')
        else:
            print(f'WARNING: {prod} is not recognised for this instrument, continuing with other prodcuts...')
