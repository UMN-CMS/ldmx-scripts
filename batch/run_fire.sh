#!/bin/bash

set -x

###############################################################################
# run_fire.sh
#   Batch running script for executing fire on a worker node and then copying
#   the results to an output directory.
###############################################################################

_job_id=$1 #should be unique between jobs submitted by the same user
_singularity_img=$2 #singularity img to use to run
_config_script=$3 #script itself to run, should be in output directory
_output_dir=$4 #output directory to copy products to, should be in /hdfs/cms/user/$USER/ldmx/
_config_args=${@:5} #arguments to configuration script, input files should be in /hdfs/cms/user/$USER/ldmx/

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
  exit 100
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
#   --cleanenv : don't copy current environment into container
if ! singularity run --no-home --bind $(pwd),/mnt/hdfs/phys/ --cleanenv $_singularity_img . fire $_config_script $_config_args; then
  echo "fire returned an non-zero error status."
  clean-up
  exit 115
fi

# Our special copying function,
#   sometimes jobs interrupt the copying mid-way through
#   (don't know why this happens)
#   but this means we need to check that the copied file
#   matches the actually generated file. This is done
#   using 'cmp -s' which does a bit-wise comparison and
#   returns a failure status upon the first mis-match.
#   
#   Sometimes (usually for larger files like ours),
#   the kernel decides to put the file into a buffer
#   and have cp return success. This is done because
#   the computer can have the copy continue on in the
#   background without interfering with the user.
#   In our case, this sometimes causes a failure because
#   we attempt to compare the copied file (which is only
#   partial copied) to the original. To solve this
#   niche issue, we can simply add the 'sync' command
#   which tells the terminal to wait for these write
#   buffers to finish before moving on.
#
#   We return a success-status of 0 if we cp and cmp.
#   Otherwise, we make sure any partially-copied files
#   are removed from the destination directory and try again
#   until the input number of tries are attempted.
#   If we get through all tries without return success,
#   then we return a failure status of 1.
#
#   Arguments
#     1 - Time in seconds to sleep between tries
#     2 - Number of tries to attempt before giving up
#     3 - source file to copy
#     4 - destination directory to put copy in
copy-and-check() {
  local _sleep_between_tries="$1"
  local _num_tries="$2"
  local _source="$3"
  local _dest_dir="$4"
  for try in $(seq $_num_tries); do
    if cp -t $_dest_dir $_source; then
      sync #wait for large files to actually leave buffer
      if cmp -s $_source $_dest_dir/$_source; then
        #SUCCESS!
        return 0;
      else
        #Interrupted during copying
        #   delete half-copied file
        rm $_dest_dir/$_source
      fi
    fi
    sleep $_sleep_between_tries
  done
  # make it here if we didn't have a success
  return 1
}

# check if output directory exists
#   we wait until here because sometimes
#   hdfs is connected when we start the job
#   but isn't connected at the end
if [[ ! -d $_output_dir ]]; then
  echo "Output directory '$_output_dir' doesn't exist!"
  exit 117
fi

# copy over each output file, checking to make sure it worked
#   most of the time this is only one file, but sometimes
#   we create both a event and a histogram file
for _output_file in *.root; do
  if ! copy-and-check 30 10 $_output_file $_output_dir; then
    # Coulding copy after trying 10 times, waiting
    #   30s between each try.
    echo "Copying failed after several tries."
    exit 118
  fi
done

clean-up
