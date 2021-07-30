# Batch at UMN
This directory contains the basic files you need to submit batch jobs to UMN through the condor system.
To get access to the pre-defined bash aliases after source the LDMX environment script, run `ldmx-condor-env` to import those commands.

In this document and the source files themselves, I use a few short-hand phrases to refer to specific things.

- `$USER` is your username. I use this shorthand because that is how it is stored in `bash`. In Python, you can get the username of whoever is running the script with `os.environ['USER']`.
- "your hdfs directory" : This refers to `/hdfs/cms/user/$USER/ldmx/`
- "your local directory" : This refers to `/local/cms/user/$USER/ldmx/`

## Production Image
First, we need to create the image that will be used to run all of the jobs.
The image you need may already exist (for example, it could be one of the releases of ldmx-sw); however, you may need to create your own production image.
The instructions for creating a production image are available [on ldmx-sw GitHub pages](https://ldmx-software.github.io/docs/custom-production-image.html).
Both ldmx-sw and ldmx-analysis have Dockerfiles that will give you a good place to start with creating a docker image and 
they both have GitHub Actions that allow each branch of the repositories to be built into docker images provided certain conditions are met.

## Config Script

The file you need to worry about editing to your specifc job a python configuration script.
We have two example configuration scripts in this directory that you can look at (more detail in the examples below).

### Output File

The batch machinery does *nothing* to determine what the name of the output file is. 
**You are responsible for making sure the output files from your batch jobs do not conflict.** 
A good habit is to have the `run_number` or `input_file` argument be used in the output file name so that you know that the output files are unique across the different jobs.

### Test Config Script and Container Image
Check to make sure your config script runs how it should run within the image you have selected.
You can do this on these machines using the following commands.
```
cd <your-local-dir>
singularity build username_repo_tag.sif docker://username/repo:tag
ln -s username_repo_tag.sif ldmx_local_my-special-tag.sif
source ldmx-sw/scripts/ldmx-env -r local -t my-special-tag
ldmx fire my-config.py <run_number-or-input_file>
```

## Submit Jobs
[HTCondor has a Python API](https://htcondor.readthedocs.io/en/latest/apis/python-bindings/) that we have used to specialize job submission to our use case of running the `fire` program.
We have aliased the running of the `submit_jobs.py` script to `ldmx-submit-jobs`, so you can use it anywhere. Run `ldmx-submit-jobs -h` for an explanation of all its parameters.

### Examples

There are three basic examples that are used regularly and are (almost) the only jobs you will need to do at the batch-running level.
These examples assume that you have made a stable installation of ldmx-sw v2.3.0 using `ldmx-make-stable`.

#### 1. Production

Here, I use the term "production" to refer to large-scale generation of simulation samples, but in general for our purposes, it simply means that the only input into your configuration is the number to use as a random seed. 
The basic idea for production is to increment through a large number of random seeds and run the same production configuration for each. 
You can see an example "production" script (although at a much smaller scale) in this directory: `production.py`.
You would submit five jobs of this production script from this directory like so. 
```
ldmx-submit-jobs -c production.py -o EXAMPLE -d ldmx/pro:v2.3.0 -n 5
```

*Comments* :
- The output directory defined using `-o` is relative to your hdfs directory (so you will find the output of these five jobs in `<your-hdfs-dir>/EXAMPLE/`. If you want the output in some other directory, you need to specify the full path.
- The version of ldmx-sw you want to use can be defined by providing the production container using a DockerHub tag (`-d`) or providing the path to the singularity file you built (`-s`).
- By default, the run numbers will start at `0` and count up from there. You can change the first run number by using the `--start_job` option. This is helpful when (for example), you want to run small group of jobs to make sure everything is working, but you don't want to waste time re-running the same run numbers.

#### 2. Analysis

Here, "analysis" could be anything that uses and input file (or files) and produces some output file (or files).
From our point of view, it doesn't matter if you are producing another event file (perhaps doing a different reconstruction for later analysis) or producing a file of histograms.
Let's analyze the files that the above script generated using the `analysis.py` script in this directory.
```
ldmx-submit-jobs -c analysis.py -o EXAMPLE/hists -i EXAMPLE -d ldmx/pro:v2.3.0 --files_per_job 2
```

*Comments*:
- Like the output directory, the input directory is also relative to your hdfs directory unless a full path is specified.
  **The current `run_ldmx.sh` script only mounts hdfs, so the container will think directories/files outside of hdfs don't exist.**
- Since there are five files to analyze and we are asking for two files per job, we will have three jobs 
(two with two files and one with one).

#### 3. Refill

This is really 1b, but since it is the most complicated, I waited until now to describe it.
Whenever there are lots of computations, little things tend to go wrong.
The most common issues on our systems are the following

- Getting kicked from a node when you are a "nice" user by a "not-nice" user.
- A job failing becuase the node it is assigned to is not connected to cvmfs or hdfs for whatever reason.

All of these issues lead to a job failing through no fault of its own.
Therefore, if you are reasonably confident that your jobs failed for these reasons,
you can "refill" any wholes in your production sequence by using this option.

Here, we assume that the run number given to the production configuration script is stored in the output file name similar to the example `production.py`: `<other-stuff>_run_<run-number>.root`.
If your output file is not formatted like this, then this option will not work.

Refill assumes that you want to refill an output directory, so simply give it an output directory and the `--refill` option and it will look through that output directory, find all the run numbers between the minimum and maximum that don't have a file, and run those run numbers.

To see that it works, delete any two of the production files that we generated (except the first and the last!) and then run the following.
```
ldmx-submit-jobs -c production.py -o EXAMPLE -d ldmx/pro:v2.3.0 -r
```

### Output
Besides the generated event or histogram files, this script will also write a few files to assist in running batch.
We put all of these generated files in the `<output-directory>/detail` directory so you can look at them later if you wish.

- `config.py`: A copy of the python configuration script you want to run. We put this here for persistency and so that the worker nodes can be reading a file that is on HDFS instead of overloading the local filesystem which is not configured to properly handle large numbers of read requests.
- `submit.<cluster-id>.log`: This is a log of what was submitted to Condor for later debugging purposes. The integer `<cluster-id>` is the number we printout upon successful submission and identifies this group of jobs.

# Extra Notes
- The `/hdfs/` directory is a file system specifically configured for a high number of different worker nodes to read from it. With this in mind, it is a good idea to have your output and input directories be a subdirectory of `/hdfs/` and the job submission program above will warn you if your input or output directory is not a subdirectory of `/hdfs/`.
- HTCondor has good documentation on [managing your jobs](https://htcondor.readthedocs.io/en/latest/users-manual/managing-a-job.html). This documentation is for a newer version of condor that we have, but you can still do most of what they describe.
- You can use the command `condor_q` to see the current status of your jobs.
- The `-long` option to `condor_q` or `condor_history` dumps all of the information about the job(s) that you have selected with the other command line options. This is helpful for seeing exactly what was run.
- If you see a long list of sequential jobs "fail", it might be that a specific worker node isn't configured properly. Check that it is one worker-node's fault by running `my-q -held -long | uniq-hosts`. If only one worker node shows up (but you know that you have tens of failed jobs), then you can `ssh` to that machine to try to figure it out (or email csehelp if you aren't sure what to do). In the mean time, you can put that machine in your list of `Machine != <full machine name>` at the top of the submit file.

# Dark Brem Signal Generation

This sample generation is a special case that requires some modification.
Normally, we want to recursively enter directories in order to get a list of all `.root` files to use as input.
The DB event libraries are directories themselves, so we need to turn off recursion.
Here is an example of submitting a job where we provide the directory hold the DB event libraries.
Notice that we need _both_ `--no_recursive` _and_ `--files_per_job 1` so that we can run the DB sim once for each event library we have.

```
ldmx-submit-jobs -c db_sim.py -d ldmx/pro:edge -i /hdfs/cms/user/eichl008/ldmx/dark-brem-event-libraries --no_recursive -o TEST --files_per_job 1 --config_args "--num_events 20000 --material tungsten"
```
