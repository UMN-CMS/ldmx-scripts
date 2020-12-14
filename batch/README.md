# Batch at UMN
This directory contains the basic files you need to submit batch jobs to UMN through the condor system.
In order to run batch jobs, there is a series of set-up steps that are necessary.

## Build Stable Installation
First, we need to create a "stable" installation of ldmx-sw so that the batch jobs can be running along in the background and you can keep doing other things. This directory has a bash script called `make_stable.sh` that will do this process for you. It can be run from (almost) anywhere, so a bash alias has been written for it in the `ldmx-env.sh` script.

When you get the source code at `/local/cms/user/$USER/ldmx/ldmx-sw/` to where you want it. Then simply run `ldmx-make-stable` to create a stable installation at `/local/cms/user/$USER/ldmx/stable-installs/` and you can move on to the next step.

## Config Script

The file you need to worry about editing to your specifc job is `config.py`.
The `config.py` file given here shows the execution of the most basic simulation we have and shows the three inputs given to the python scriopt automatically by the submission script. These three inputs (the argparse stuff at the top) is _necessary_ to be able to run your script.

Input | Description
---|---
`input_file` | If an input file for the run is given, this argument is set to the name of the input file after it is copied over to the working directory.
`run_number` | Passed as the run number from the `ldmx_write_jobs.py`. Look there if you wish to control how these run numbers are generated.

You can feel free to add other arguments here as well, but since these arguments need to interact with the other parts of the batch machinery, they are _required_.

The batch machinery does *nothing* to determine what the name of the output file is. *You are responsible for making sure the output files from your batch jobs do not conflict.* A good habit is to have the `run_number` argument be used in the output file name so that you know that the output files are unique across the different numbered jobs.

### Test Config Script
Check to make sure your config script and your stable installation run how you thinkthink it should. Make sure to open a new terminal so that you are starting from a clean environment (like the worker nodes will be).
```
source /local/cms/user/$USER/ldmx/stable-installs/<install-name>/setup.sh
fire my-config.py
```

## Write Job List

Condor retrieves a list of jobs from a submission file. Familiarizing yourself with the primitive programming that Condor uses to parse this submission file is very helpful becuase it can simplify the submission file and lead to less errors. Condor has pretty [good documentation](https://htcondor.readthedocs.io/en/latest/users-manual/submitting-a-job.html#submitting-many-similar-jobs-with-one-queue-command) on how to write this submission file.

But to help you get started, there is a simple python script `ldmx_write_jobs.py` that can write a submission file for you from the given inputs.

## Submit the Job List

Now you can submit the jobs to the cluster by running the following command.
```
condor_submit <job_list.sub>
```
It is _highly_ recommend for you to save the job list. It will help if you need to re-run the same jobs or if you want to debug if anything went wrong.

# Extra Notes
- To prevent overloading the file system, your job should copy any input files to the worker node (probably to a scratch directory of some kind), write any output into that working directory, and then copy the output to the desired output directory. This is already done in the script that is used to run the jobs by default `run_fire.sh`, but it is hightlighted here for you if you want to do something else.
- You can use the command `condor_q` to see the current status of your jobs.
- The `-long` option to `condor_q` or `condor_history` dumps all of the information about the job(s) that you have selected with the other command line options. This is helpful for seeing exactly what was run.
