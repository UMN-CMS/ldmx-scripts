#!/bin/bash

###############################################################################
# group_files.sh
#   Prints all the files in the input directory separated onto lines
#   such that the input number of files is the maximum number on each
#   line
###############################################################################

if [[ "$1" =~ ^[0-9]+$ ]]
then
  _nfiles_per_line="$1"
else
  exit 1
fi

if [ -d $2 ]
then
  _directory=$(cd $2 &> /dev/null; pwd)
else
  exit 1
fi

_files_on_current_line=0
for f in $_directory/*
do
  if [ -f "$f" ]
  then
    # this listing in the directory is a file
    #   -> print it onto the current line
    _files_on_current_line=$((_files_on_current_line+1))
    printf "$f "

    if [ $_files_on_current_line -eq $_nfiles_per_line ]
    then
      # we reached the number of files per line
      #   -> print new line and reset counter
      printf "\n"
      _files_on_current_line=0
    fi
  fi
done

if [ $_files_on_current_line -gt 0 ]
then
  # make new line for extra files
  printf "\n"
fi
