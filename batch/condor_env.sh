#!/bin/bash

################################################################################
# Setup Condor Batch environment for ldmx-sw
################################################################################

# helpful alias for making a stable installation
alias ldmx-make-stable='bash $LDMX_ENV_DIR/batch/make_stable.sh'

# helpful alias for writing batch job lists
alias ldmx-write-jobs='python3 $LDMX_ENV_DIR/batch/write_jobs.py'

# list missing run numbers from the input directory of files
alias missing-runs='python3 $LDMX_ENV_DIR/batch/missing_runs.py'

# look at my job listing
alias my-q='condor_q -submitter $USER'

# check the totals of the job listing
alias my-q-totals='my-q -totals'

# watch the job totals
alias watch-q='watch condor_q -submitter $USER -totals'

# rm non-running jobs
condor_rm_held() {
  condor_rm -constraint 'JobStatus == 5'
}

# Release all jobs submitted by you
alias release-me='condor_release $USER'

# Get the list of uniq hosts from the input file of long condor logs
#   e.g. my-q -long | uniq-hosts
alias uniq-hosts='grep RemoteHost | sort -u | cut -d " " -f 3'

# Count the number of root files in the input directory
file-count() {
  ls -1 "$1"*.root | wc -l
}

# get the exit codes from the passed cluster of jobs (number before the .)
exit-codes() {
  condor_history -long $1 | grep "ExitCode" | sort -u | awk '{printf "%d ", $NF} END {printf "\n"}'
}

# get the list of missing numbers from a list of sequential numbers
missing-nums() {
  awk 'NR != $1 + 1 { for (i = prev; i < $1; i++) {print i} } { prev = $1 + 1 }' $@
}
