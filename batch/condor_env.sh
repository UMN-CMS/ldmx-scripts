#!/bin/bash

################################################################################
# Setup Condor Batch environment for ldmx-sw
################################################################################

# helpful alias for making a stable installation
alias ldmx-make-stable='bash $LDMX_ENV_DIR/batch/make_stable.sh'

# helpful alias for submitting batch jobs
alias ldmx-submit-jobs='python3 $LDMX_ENV_DIR/batch/submit_jobs.py'

# look at my job listing
alias my-q='condor_q -submitter $USER'

# check the totals of the job listing
alias my-q-totals='my-q -totals'

# watch the job totals
alias watch-q='watch condor_q -submitter $USER -totals'

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
