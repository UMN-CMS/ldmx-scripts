#!/bin/bash

set -x

###############################################################################
# run_fire_from_scratch.sh
#   Batch running script for executing fire on a worker node and then copying
#   the results to an output directory.
###############################################################################

_job_id=$1 #should be unique between jobs submitted by the same user
_env_script=$2 #environment to use, ignored in this run mode
_config_script=$3 #script itself to run, should be in output directory
_output_dir=$4 #output directory to copy products to, should be in /hdfs/cms/user/$USER/ldmx/
_config_args=${@:5} #arguments to configuration script, input files should be in /hdfs/cms/user/$USER/ldmx/

if [[ ! -d /cvmfs/cms.cern.ch || ! -d /hdfs/cms/user ]]; then
  echo "Worker node is not connected to cvmfs and/or hdfs."
  exit 99
fi

# make sure we go to our scratch area
_scratch_root=/export/scratch/users/$USER/
mkdir -p $_scratch_root
cd $_scratch_root

# setup our scratch install of ldmx-sw
if ! source ldmx-container/setup.sh; then
  echo "Wasn't able to source the environment script."
  exit 111
fi

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

if ! fire $_config_script $_config_args; then
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
#   We return a success-status of 0 if we cp and cmp.
#   Otherwise, we make sure any partially-copied files
#   are removed from the destination directory and try again.
#
#   Arguments
#     1 - Time in seconds to sleep between tries
#     2 - Number of tries to attempt before giving up
#     3 - source file to copy
#     4 - destination directory to put copy in
copy-and-check() {
  _sleep_between_tries="$1"
  _num_tries="$2"
  _source="$3"
  _dest_dir="$4"
  for try in seq $_num_tries
  do
    if cp $_source $_dest_dir; then
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

# copy over each output file, checking to make sure it worked
#   most of the time this is only one file, but sometimes
#   we create both a event and a histogram file
for _output_file in *.root
do
  if ! copy-and-check 30 10 $_output_file $_output_dir; then
    # Coulding copy after trying 10 times, waiting
    #   30s between each try.
    echo "Copying failed after several tries."
    exit 118
  fi
done

clean-up
