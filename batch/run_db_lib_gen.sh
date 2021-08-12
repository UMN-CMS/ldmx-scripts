#!/bin/bash

set -x

###############################################################################
# run_db_lib_gen.sh
#   Batch running script for executing commands on a worker node inside a
#   singularity container and then copying the output root file(s) to an
#   output directory.
###############################################################################

_job_id=$1 #should be unique between jobs submitted by the same user
_singularity_img=$2 #singularity img to use to run, should be in /local/cms/user/$USER/ldmx/
_output_dir=$3 #output directory to copy products to, should be in /hdfs/cms/user/$USER/ldmx/
_args=${@:4} #arguments to container, input files should be in /hdfs/cms/user/$USER/ldmx/

if [[ ! -d /hdfs/cms/user ]]; then
  echo "Worker node is not connected to hdfs."
  exit 99
fi

if ! hash singularity &> /dev/null; then
  echo "Worker node does not have singularity installed."
  exit 99
fi

# make sure we go to our scratch area
_scratch_root=/export/scratch/users/$USER/
mkdir -p $_scratch_root
cd $_scratch_root

# cleanup the directory if it already exists
#   (it shouldn't)
if [[ -d $_job_id ]]; then
  rm -r $_job_id
fi

# make the working directory for this job and go into it
mkdir $_job_id
if ! cd $_job_id; then
  echo "Can't setup working directory."
  exit 98
fi

# Now that we have entered our working directory,
#   clean-up entails exiting the directory for this
#   specific job and deleting the whole thing.
clean-up() {
  cd $_scratch_root
  rm -r $_job_id
}

# Singularity command to run the fire executable
#   --no-home : don't mount home directory
#   --bind : mount our current directory and /hdfs/ (for reading input files)
singularity run --no-home --bind $(pwd):/working_dir,${_output_dir} $_singularity_img --out_dir ${_output_dir} $_args || exit $?

clean-up
