#!/bin/bash

################################################################################
# Setup Condor Batch environment for ldmx-sw
################################################################################

# helpful alias for making a stable installation
alias ldmx-make-stable='bash $LDMX_ENV_DIR/batch/make_stable.sh'

# helpful alias for submitting batch jobs
#   some weird condor configuration requires us to submit from scorpions
#   so make sure to 'ssh scorpion1' before this
alias ldmx-submit-jobs='python3 $LDMX_ENV_DIR/batch/submit_jobs.py'

# Launching everything from scorpion1 since zebras have been
#   disconnected from HTCondor
alias condor_q='ssh scorpion1 condor_q'
alias condor_rm='ssh scorpion1 condor_rm'

# look at my job listing
alias my-q='condor_q -submitter $USER'

# check the totals of the job listing
alias my-q-totals='my-q -totals'

# watch the job totals
alias watch-q='watch -n 30 ssh scorpion1 condor_q -submitter $USER -totals'

# Count the number of root files in the input directory
file-count() {
  ls -f "$1" | wc -l
}

# get the exit codes from the passed cluster of jobs (number before the .)
exit-codes() {
  condor_history -long $1 | grep "ExitCode" | sort -u | awk '{printf "%d ", $NF} END {printf "\n"}'
}

# get the list of missing numbers from a list of sequential numbers
missing-nums() {
  awk 'NR != $1 + 1 { for (i = prev; i < $1; i++) {print i} } { prev = $1 + 1 }' $@
}

# Add our python modules to the PYTHONPATH to make things easier to run
export PYTHONPATH=$PYTHONPATH:$LDMX_ENV_DIR/batch/python/

# define a helpful variable for make_stable.sh and accessing the stable installations
export LDMX_STABLE_INSTALLS=$LDMX_BASE/stable-installs

# check that the input host has hdfs and cvmfs
check-host() {
  _host="$1"
  echo -n "$_host..."
  if ! ssh -q $_host 'if [[ ! -d /cvmfs/cms.cern.ch ]]; then echo "No cvmfs"; elif [[ ! -d /hdfs/cms/user ]]; then echo "No hdfs"; else echo "good"; fi'
  then
    echo "Can't connect"
  fi
}

# check all the scorpions
check-scorpions() {
  for scorpion in scorpion{1..48}; do check-host $scorpion; done
}

# clean the host's /export/scratch/users directory by removing this user's working directory
clean-host() {
  _host="$1"
  echo -n "$_host..."
  if ! ssh -q $_host "cd /export/scratch/users; if [[ -d $USER ]]; then rm -r $USER; echo 'cleaned'; else echo 'No user dir'; fi"
  then
    echo "Can't connect"
  fi
}

# clean all of the scorpions
#   Don't run this while you have any jobs running!!!
clean-scorpions() {
  for scorpion in scorpion{1..48}; do clean-host $scorpion; done
}

# List jobs that failed to copy
failed-copy() {
  my-q -held -constraint 'HoldReasonSubCode == 118' $@
}

# Archive log files for the input cluster
archive-logs() {
  _cluster="$1"
  tar --create --remove-files --verbose --file $_cluster.tar.gz $_cluster-*
}
