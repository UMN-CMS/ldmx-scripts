#!/bin/bash

# SUGGESTION:
#   Put the following command in your .bashrc file to make setting up
#   the ldmx environment easier
#   alias ldmx-env='source <path-to-this-file>/ldmx-env.sh; unalias ldmx-env'

# get the directory of this script
export LDMX_ENV_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"

# This is the full path to the directory containing ldmx-sw
_base="$( cd "${LDMX_ENV_DIR}/../" &>/dev/null && pwd)"

# Setup container environment
if ! source $_base/ldmx-sw/scripts/ldmx-env.sh -b $_base $@; then
  echo "ERROR from container setup script."
  return 1
fi

# prepends fire with valgrind to check for memory leaks
alias ldmx-val='valgrind --tool=memcheck --leak-check=yes --suppressions=$ROOTSYS/etc/root/valgrind-root.supp --log-file=memcheck.log fire'

# skips directories that aren't modules
#   now run 'grepmodules <pattern>' in ldmx-sw/ to search for a <pattern> in the module source files
alias grepmodules='grep --exclude-dir=build --exclude-dir=docs --exclude-dir=install --exclude-dir=.git -rHn'

# setup the condor batch environemtn
alias ldmx-condor-env='source $LDMX_ENV_DIR/batch/condor_env.sh; unalias ldmx-condor-env'

# remove all the files listed in install_manifest.txt
alias ldmx-clean-install='xargs rm < install_manifest.txt'

# A safe copy where we make sure that the copy succeeded
safe-cp() {
  local _file="$1"
  local _dest_dir="$2"
  echo -n "$_file..."
  if cp -t $_dest_dir $_file; then
    sync
    if cmp -s $_dest_dir/$_file $_file; then
      echo "success!"
      return 0
    else
      echo "failed on cmp"
      #remove non-matching destination file
      rm $_dest_dir/$_file
    fi
  else
    echo "failed on cp"
    #remove failed copy (if it exists)
    # sometimes cp leaves a partially copied file behind
    if [[ -f $_dest_dir/$_file ]]; then
      rm $_dest_dir/$_file;
    fi
  fi
  return 1
}

# Safely move a file, making sure the copy succeeded
safe-mv() {
  local _file="$1"
  local _dest_dir="$2"
  if safe-cp $_file $_dest_dir; then
    rm $_file
  fi
}
