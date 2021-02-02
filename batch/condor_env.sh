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
condor_q() {
  ssh scorpion1 "condor_q $@"
}
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

# Add our python modules to the PYTHONPATH to make things easier to run
export PYTHONPATH=$PYTHONPATH:$LDMX_ENV_DIR/batch/python/

# define a helpful variable for make_stable.sh and accessing the stable installations
export LDMX_STABLE_INSTALLS=$LDMX_BASE/stable-installs

# check that the input host has hdfs and cvmfs
check-host() {
  local _host="$1"
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
  local _host="$1"
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

# print the disk space for the /export/scratch directory of the input host
scratch-space-on-host() {
  local _host="$1"
  echo -n "$_host : "
  if ! ssh -q $_host "df -h /export/scratch | sed 1d"
  then
    echo "Can't connect"
  fi
}

# print the disk space on all the scorpions
list-scorpion-scratch-space() {
  for scorpion in scorpion{1..48}; do scratch-space-on-host $scorpion; done
}

# List jobs that failed to copy
failed-copy() {
  my-q -held -constraint 'HoldReasonSubCode == 118' $@
}

# Archive log files for the input cluster
archive-logs() {
  local _cluster="$1"
  tar --create --remove-files --verbose --file $_cluster.tar.gz $_cluster-*
}

# Manually go to a remote and get the finished file
manual-copy() {
  local _remote="$1"
  local _cluster="$2"
  local _process="$3"
  local _dest="/local/cms/user/$USER"
  echo -n "$_remote (${_cluster}-${_process})..."
  if ! ssh -q $_remote "cd /export/scratch/users; if [[ -d $USER ]]; then cd $USER; if [[ -d ${_cluster}-${_process} ]]; then cd ${_cluster}-${_process}; for _f in *.root; do if cp -t $_dest $_f && sync && cmp -s $_f $_dest/$_f; then echo 'success'; else echo 'failed to copy'; fi; done; else echo 'No job dir'; fi; else echo 'No user dir'; fi"
  then
    echo "Can't connect"
  fi
}
