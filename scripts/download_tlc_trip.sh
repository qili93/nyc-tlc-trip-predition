#!/bin/bash

# usage:
# bash scripts/download_tlc_trip.sh ./data
set -e

if [ -z "$1" ]; then
  echo "usage scripts/download_tlc_trip.sh [data dir]"
  exit
fi

# Create the output directories.
OUTPUT_DIR="${1%/}"
mkdir -p "${OUTPUT_DIR}"
CURRENT_DIR=$(pwd)

# Download function

function download_data () {
  local BASE_URL=${1}
  local FILENAME=${2}
  
  if [ ! -f ${FILENAME} ]; then
    echo "Downloading ${FILENAME} to $(pwd)"
    wget -nd -c "${BASE_URL}/${FILENAME}"
  else
    echo "Skipping download of ${FILENAME}"
  fi
}

cd ${OUTPUT_DIR}

# Download
BASE_IMAGE_URL="https://s3.amazonaws.com/nyc-tlc/trip+data"

for i in $(seq -f "%02g" 1 12)
do 
  DATA_FILE_NAME="yellow_tripdata_2018-"$i".csv"
  download_data $BASE_IMAGE_URL $DATA_FILE_NAME
done

echo "Download Finished"



