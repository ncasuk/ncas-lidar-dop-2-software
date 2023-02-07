#!/bin/bash

#
# ./make_netcdf.sh YYYYmmdd
#

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

gws_path=/gws/pw/j07/ncas_obs_vol1

netcdf_path=${gws_path}/iao/processing/ncas-lidar-dop-2/netcdf_files
datapath=${gws_path}/iao/raw_data/ncas-lidar-dop-2/incoming/Proc
logfilepath=${gws_path}/iao/logs/ncas-lidar-dop-2

metadata_file=${SCRIPT_DIR}/../metadata.csv


datadate=$1  # YYYYmmdd
conda_env=${2:-netcdf}

conda activate ${conda_env}

year=${datadate:0:4}
month=${datadate:4:2}
day=${datadate:6:2}

stare_files=$(ls ${datapath}/${year}/${year}${month}/${datadate}/Stare*)
no_stare_files=$(ls ${datapath}/${year}/${year}${month}/${datadate}/Stare* | wc -l)
wp_files=$(ls ${datapath}/${year}/${year}${month}/${datadate}/Wind_Profile*)
no_wp_files=$(ls ${datapath}/${year}/${year}${month}/${datadate}/Wind_Profile* | wc -l)

python ${SCRIPT_DIR}/../process_lidar_stare.py ${stare_files} -m ${metadata_file} -o ${netcdf_path} -v
python ${SCRIPT_DIR}/../process_lidar_wind_profile.py ${wp_files} -m ${metadata_file} -o ${netcdf_path} -v


if [ -f ${netcdf_path}/ncas-lidar-dop-2_iao_${year}${month}${day}_aerosol-backscatter-radial-winds_stare_*.nc ]
then 
  stare_file_exists=True
else
  stare_file_exists=False
fi

if [ -f ${netcdf_path}/ncas-lidar-dop-2_iao_${year}${month}${day}_aerosol-backscatter-radial-winds_wind-profile*.nc ]
then 
  wp_file_exists=True
else
  wp_file_exists=False
fi

if [ -f ${netcdf_path}/ncas-lidar-dop-2_iao_${year}${month}${day}_mean-winds-profile*.nc ]
then 
  mwp_file_exists=True
else
  mwp_file_exists=False
fi



cat << EOF | sed -e 's/#.*//; s/  *$//' > ${logfilepath}/${year}${month}${day}.txt
Date: $(date -u)
Number of stare files: ${no_stare_files}
Number of wind profile files: ${no_wp_files}
stare file created: ${stare_file_exists}
wind profile file created: ${wp_file_exists}
mean winds profile file created: ${mwp_file_exists}
EOF
