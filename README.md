# ncas-lidar-dop-2-software

Code for creating AMOF-compliant netCDF files for ncas-lidar-dop-2 instrument.

## Requirements
* python 3.7 or above
* modules:
  * netCDF4
  * numpy
  * datetime
  * parse
  * [ncas-amof-netcdf-template]


## Installation

Clone the git repo:
```
git clone https://github.com/joshua-hampton/ncas-lidar-dop-2-software.git
```

Install required modules using `pip install -r requirements.txt` or `conda install --file requirements.txt -c conda-forge`


## Usage

Two processing scripts are supplied, for when the lidar is in "Stare" mode or "Wind Profile" mode. All raw data files for a day are to be supplied to the python scripts.

Additional metadata can be supplied in the `metadata.csv` file.

To use each python script, from the command line:
```
python process_lidar_stare.py /path/to/stare_raw_file1.hpl /path/to/stare_raw_file2.hpl ... -m metadata.csv
python process_lidar_wind_profile.py /path/to/wind_profile_raw_file1.hpl /path/to/wind_profile_raw_file2.hpl -m metadata.csv
```
Additional flags that can be given for each python script:
* `-o` or `--ncfile-location` - where to write the netCDF files to. If not given, default is `'.'`
* `-v` or `--verbose` - print additional information as the script runs


A description of all the available options can be obtained using the `-h` flag, for example
```
python process_lidar_stare.py -h
```

### BASH scripts

Three [scripts] are provided for easy use:
* `make_netcdf.sh` - makes netCDF file for a given date: `./make_netcdf.sh YYYYmmdd`
* `make_today_netcdf.sh` - makes netCDF file for today's data: `./make_today_netcdf.sh`
* `make_yesterday_netcdf.sh` - makes netCDF file for yesterday's data: `./make_yesterday_netcdf.sh`

Within `make_netcdf.sh`, the following may need adjusting:
* `netcdf_path="/gws/..."`: replace file path with where to write netCDF files.
* `datapath="/gws/..."`: replace file path with path to data.
* `metadata_file=${SCRIPT_DIR}/../metadata.csv`: replace if using different metadata file.
* `logfilepath="/home/..."`: replace with path of where to write logs to


[scripts]: scripts

## Further Information

* `read_lidar.py` contains the code that actually reads the raw data. This is called from within the process lidar scripts.
* Some quality control is performed on the aerosol-backscatter-radial-winds data product. No quality control is currently done on any other product.

[ncas-amof-netcdf-template]: https://ncas-amof-netcdf-template.readthedocs.io/en/stable 
