# Example Condor Submission Files

This directory contains a few more complicated condor submission files that can be used as templates instead of using the python script to write a new one.

### production.sub

This submission file runs several jobs of "production" where there is no input files and we are simply generating data (usually via simulation).

#### Assumptions
All of these assumptions can be changed in the file itself, but I've found these to be a good starting point.

- The output directory is `/hdfs/cms/user/$USER/ldmx/MY_OUTPUT_DIRECTORY`
- The configuration for running the job is at `<output-directory>/details/config.py`
- `config.py` takes one command line argument: the run number that job should use
- The `ldmx-scripts` repository (this repository) is in `/local/cms/user/$USER/ldmx/`.

#### Usage
This submission script can be used in several ways. Here, I document the command line input in the bash style.
```
condor_submit [start_job=START | refill=YES ] [save_output=DIR] production.sub [-queue NJOBS]
```

Option | Description
---|---
`start_job` | `START` is an integer on which to start the run number counting. *Ignored if `refill` is used.*
`refill` | Look through the output directory and re-run any run numbers that are missing. *Look at the `missing_runs.py` script for how the run numbers are determined.*
`save_output` | Prints the terminal output of the program to `DIR/<cluster-num>-<process-num>.out`.
`-queue` | Submits `NJOBS` iterating the run number each time. *Should not be used with `refill`.*

### analysis.sub

This submission file runs several jobs of "analysis" where we run a configuration over the input files given to it on the command line.

#### Assumpitons
All of these assumptions can be changed in the file itself, but I've found these to be a good starting point.

- The output directory is `/hdfs/cms/user/$ENV(USER)/ldmx/MY_ANALYSIS_HISTS`
- The configuration for running the job is at `<output-directory>/details/config.py`
- `config.py` takes the list of input files it shoud run over as its only command line arguments
- The `ldmx-scripts` repository (this repository) is in `/local/cms/user/$USER/ldmx/`.
- The input directories are listed at the bottom of the file in place of `PUT_INPUT_DIRECTORIES_HERE`. This list is space-separated and should be full paths. Feel free to use the variables defined earlier in the script (e.g. `$(hdfs_dir)`).

#### Usage
This submission script can be used in several ways. Here, I document the command line input in the bash style.
```
condor_submit [nfiles_per_job=NPER] [max_jobs=MAX] [save_output=DIR] production.sub
```

Option | Description
---|---
`nfiles_per_job` | `NPER` is the number of files to group into one analysis job. Default is 10.
`max_jobs` | `MAX` is the maximum number of jobs to run. Default is to do as many jobs as needed to process all files in the input director{y,ies}.
`save_output` | Prints the terminal output of the program to `DIR/<cluster-num>-<process-num>.out`.
