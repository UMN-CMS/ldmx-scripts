#!/bin/bash

# SUGGESTION:
#   Put the following command in your .bashrc file to make setting up
#   the ldmx environment easier
#   alias ldmx-env='source <path-to-this-file>/ldmx-env.sh; unalias ldmx-env'

# get the directory of this script
export LDMX_ENV_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"

# use the larger export scratch for temp working
export TMPDIR=/export/scratch/users/$USER
mkdir -p $TMPDIR

# This is the full path to the directory containing ldmx-sw on local
_base="$( cd "${LDMX_ENV_DIR}/../" &>/dev/null && pwd)"

# Check for /export/scratch copy for working on interactive node
_interactive_base="/export/scratch/users/$USER/ldmx"
if [[ -d ${_interactive_base}/ldmx-sw ]]; then
  _base="${_interactive_base}"
fi

# define cache location
export SINGULARITY_CACHEDIR=$_base/.singularity

# Setup container environment
if ! source $_base/ldmx-sw/scripts/ldmx-env.sh -b $_base $@; then
  echo "ERROR from container setup script."
  return 1
fi

# Other helpful aliases and functions below

# skips directories that aren't modules
#   now run 'grepmodules <pattern>' in ldmx-sw/ to search for a <pattern> in the module source files
alias grepmodules='grep --exclude-dir=build --exclude-dir=docs --exclude-dir=install --exclude-dir=.git -rHn'

# setup the condor batch environemtn
alias ldmx-condor-env='source $LDMX_ENV_DIR/batch/condor_env.sh; unalias ldmx-condor-env'

# remove all the files listed in install_manifest.txt
alias ldmx-clean-install='xargs rm < install_manifest.txt'
