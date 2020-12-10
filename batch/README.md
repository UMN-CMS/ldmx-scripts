# Batch at UMN
This directory contains the basic files you need to submit batch jobs to UMN through the condor system.
In order to run batch jobs, there is a series of set-up steps that are necessary.

## Build Stable Installation
First, we need to create a "stable" installation of ldmx-sw so that the batch jobs can be running along in the background and you can keep doing other things. This directory has a bash script called `make_stable.sh` that will do this process for you. It can be run from (almost) anywhere, so it is helpful to define a bash alias for this script in your `~/.bashrc`.
`alias ldmx-make-stable='bash /local/cms/user/$USER/ldmx/ldmx-scripts/batch/make_stable.sh'`

When you get the source code at `/local/cms/user/$USER/ldmx/ldmx-sw/` to where you want it. Then simply run `ldmx-make-stable` to create a stable installation at `/local/cms/user/$USER/ldmx/stable-installs/` and you can move on to the next step.

## Config Script

The file you need to worry about editing to your specifc job is `config.py`.
The `config.py` file given here shows the execution of the most basic simulation we have and shows the three inputs given to the python scriopt automatically by the submission script. These three inputs (the argparse stuff at the top) is _necessary_ to be able to run your script.

Input | Description
---|---
`input_file` | If an input file for the run is given, this argument is set to the name of the input file after it is copied over to the working directory.
`run_number` | Passed as the run number from the `ldmx_write_jobs.py`. Look there if you wish to control how these run numbers are generated.

You can feel free to add other arguments here as well, but since these three arguments need to interact with the other parts of the batch machinery, they are _required_.

## Write Job List

Condor works by submitting a list of jobs to run. You can write a list of jobs using the python executable `ldmx_write_jobs.py`.
Use the following to get a full explanation of the options.
```
./ldmx_write_jobs.py -h
```
Skim through this list to double check that the arguments given to the jobs make sense. You can technically run `ldmx_write_jobs.py` from anywhere, so again it is helpful to add a bash alias to your `.bashrc`: 
`alias ldmx-write-jobs='python /local/cms/user/$USER/ldmx/ldmx-scripts/batch/ldmx_write_jobs.py'`.

## Submit the Job List

Now you can submit the jobs to the cluster by running the following command.
```
condor_submit <job_list.sub>
```
It is _highly_ recommend for you to save the job list. It will help if you need to re-run the same jobs or if you want to debug if anything went wrong.

# Extra Notes
- To prevent overloading the file system, your job should copy any input files to the worker node (probably to a scratch directory of some kind), write any output into that working directory, and then copy the output to the desired output directory.
- You can use the command `condor_q` to see the current status of your jobs.
