# ncas-lidar-dop-2-software

Code for creating AMOF-compliant netCDF files for ncas-lidar-dop-2 instrument.

Uses [ncas_amof_netcdf_template] submodule to create an empty netCDF file.

## Requirements
* python
* modules:
  * netCDF4
  * numpy
  * datetime
  * parse


## Installation

Clone the git repo and submodule:
```
git clone --recurse-submodules https://github.com/joshua-hampton/ncas-lidar-dop-2-software.git
```

If the `--recurse-submodules` flag is not included, the `ncas_amof_netcdf_template` repo will not also be cloned. To fix this, use the following commands in the top level of this repo:
```
git submodule init
git submodule update
```

**TO DO**

Install required modules using `pip install -r requirements.txt` or `conda install --file requirements.txt`


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

**TO DO**

Bash scripts to help automate this.


[ncas_amof_netcdf_template]: https://github.com/joshua-hampton/ncas_amof_netcdf_template
