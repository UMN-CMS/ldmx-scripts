#!/bin/bash

set -ex

###############################################################################
# run_fire.sh
#   Batch running script for executing fire on a worker node and then copying
#   the results to an output directory.
###############################################################################

_env_script=$1 #environment to use
_config_script=$2 #script itself to run
_output_dir=$3 #output directory to copy products to
_input_file=$4 #optional
_config_args=${@:4} #arguments to configuration script

_scratch_area=/export/scratch/users/eichl008
if ! mkdir -p $_scratch_area
then
    echo "Can't find scratch area!"
    exit 110
fi
cd $_scratch_area

# Get a unique working directory from the
#   current date and time and PID
# This is probably overkill, but wanted
#   to make sure
_unique_working_dir="$(date +%Y-%M-%d-%H-%M)-pid-$$"
mkdir -p $_unique_working_dir
cd $_unique_working_dir

if [[ ! -z "$(ls -A .)" ]]
then
  # temp directory non-empty
  #   we need to clean it before running so that
  #   the only files are the ones we know about
  rm -r *
fi

_to_remove="__pycache__"
if [[ -f $_input_file ]]
then
  # the fourth argument is actually a file, so
  #   copy that input file here and then shift
  #   the rest of the config args accordingly
  cp $_input_file .
  _input_file=$(basename $_input_file)
  _to_remove="$_to_remove $_input_file"
  _config_args="${_config_args:2} --input_file $_input_file"
fi

cp $_config_script .
_config_script=$(basename $_config_script)
_to_remove="$_to_remove $_config_script"

source $_env_script

fire \
  $_config_script \
  $_config_args

# first remove the input files
#   so they don't get copied to the output
rm -r $_to_remove

# copy all other generated root files to output
cp *.root $_output_dir

# clean up unique working dir
cd ..
rm -r $_unique_working_dir
