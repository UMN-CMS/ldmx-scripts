"""Submitting jobs for ldmx to Condor batch submission

This python script is intended to be used with the running script 'run_fire.sh' in this current directory.
"""

import os
import argparse
from umn_htcondor.utility import local_dir, hdfs_dir
from umn_htcondor.submit import JobInstructions

parser = argparse.ArgumentParser('ldmx-submit-jobs',
    description="Submit batches of jobs running the ldmx-sw application.",
    formatter_class=argparse.RawDescriptionHelpFormatter)

# required args
parser.add_argument("-c",metavar='CONFIG',dest='config',required=True,type=str,help="CONFIG is python configuration script to run.")
parser.add_argument("-o",metavar='OUT_DIR',dest='out_dir',required=True,type=str,help="OUT_DIR is directory to copy output to. If the path given is relative (i.e. does not begin with '/'), then we assume it is relative to your hdfs directory: %s"%hdfs_dir())

environment = parser.add_mutually_exclusive_group(required=True)
environment.add_argument('-e',metavar='ENV_SCRIPT',dest='env_script',type=str,help="Environment script to run before running fire.")
environment.add_argument('-l',metavar='LDMX_VERSION',dest='ldmx_version',type=str,help="LDMX Version to pick a pre-made environment script.")

how_many_jobs = parser.add_mutually_exclusive_group(required=True)
how_many_jobs.add_argument('-i',metavar='INPUT_DIR',dest='input_dir',type=str,nargs='+',help="Directory containing input files to run over. If the path given is relative (i.e. does not begin with '/'), then we assume it is relative to your hdfs directory: %s"%hdfs_dir())
how_many_jobs.add_argument('-n',metavar='NUM_JOBS',dest='num_jobs',type=int,help="Number of jobs to run (if not input directory given).")
how_many_jobs.add_argument('-r','--refill',dest='refill',action='store_true',help="Look through the output directory and re-run any run numbers that are missing.")

# optional args for configuring how the job runs
parser.add_argument("--input_arg_name",type=str,default='',help='Name of argument that should go before the input file or run number when passing it to the config script.')
parser.add_argument("--start_job",type=int,default=0,help="Starting number to use when run numbers. Only used if NOT running over items in a directory.")
parser.add_argument("--files_per_job",type=int,default=10,help="If running over an input directory, this argument defines how many files to group together per job.")
parser.add_argument("--max_num_jobs",type=int,default=1000,help="If running over an input directory, this argument defines the maximum number of jobs to submit at once.")

# rarely-used optional args
full_path_to_dir_we_are_in=os.path.dirname(os.path.realpath(__file__))
parser.add_argument("--run_script",type=str,help="Script to run jobs on worker nodes with.",default='%s/run_fire.sh'%full_path_to_dir_we_are_in)
parser.add_argument("--config_args",type=str,default='',help="Extra arguments to be passed to the configuration script. Passed after the run_number or input_file.")
parser.add_argument("--nocheck",action='store_true',help="Don't pause to look at job details before submitting.")
parser.add_argument("--test",action='store_true',help="Just print Job details to terminal, don't actually submit.")
parser.add_argument("--save_output",type=str,help="Save terminal output to the input directory. Only use for debugging purposes. This can over-burden the filesystem is used with too many (>10) jobs.")
parser.add_argument("--nonice",action='store_true',dest="nonice",help="Do not run this at nice priority.")
parser.add_argument("--sleep",type=int,help="Time in seconds to sleep before starting the next job.",default=5)
parser.add_argument("--max_memory",type=str,default='4G',help='Maximum amount of memory to give jobs. Can use \'K\', \'M\', \'G\' as suffix specifiers.')
parser.add_argument("--max_disk",type=str,default='4G',help='Maximum amount of disk space to give jobs. Can use \'K\', \'M\', \'G\' as suffix specifiers.')
parser.add_argument("--periodic_release",action='store_true',help="Periodically release any jobs that exited because the worker node was not connected to cvmfs or hdfs.")

machine_choice = parser.add_mutually_exclusive_group()
machine_choice.add_argument("--broken_machines",type=str,nargs='+',help="Extra list of machines that should be avoided, usually because they are not running your jobs for whatever reason. For example: --broken_machines scorpion34 scorpion17")
machine_choice.add_argument("--useable_machines",type=str,nargs='+',help="List of machines that should be used, no other machines are allowed. For example: --useable_machines scorpion{1..9}")
machine_choice.add_argument("--check_n_pick",action='store_true',help='Loop through the scorpions and ban any machines that arent connected to cvmfs or hdfs.')

arg = parser.parse_args()

if arg.env_script is not None :
    env_script = os.path.realpath(arg.env_script)
else :
    env_script = '%s/stable-installs/%s/setup.sh'%(local_dir(),arg.ldmx_version)

job_instructions = JobInstructions(arg.run_script, arg.out_dir, env_script, arg.config, 
    input_arg_name = arg.input_arg_name, extra_config_args = arg.config_args)

job_instructions.memory(arg.max_memory)
job_instructions.disk(arg.max_disk)
job_instructions.nice(not arg.nonice)
job_instructions.sleep(arg.sleep)

if arg.check_n_pick :
    check_cmd = "'if [[ -d /cvmfs/cms.cern.ch && -d /hdfs/cms/user && -f %s/setup.sh ]]; then exit 0; else exit 1; fi'"%os.environ["LDMX_CONTAINER_DIR"]
    for s in range(1,49) :
        host = f'scorpion{s}'
        if os.system(f'ssh -q {host} {check_cmd}') != 0 :
            job_instructions.ban_machine(host)
elif arg.broken_machines is not None :
    # Add additional machines to avoid using
    for m in arg.broken_machines :
        job_instructions.ban_machine(m)
elif arg.useable_machines is not None :
    # Reset requirements
    job_instructions['requirements'] = 'False'
    for m in arg.useable_machines :
        job_instructions.use_machine(m)

# run_fire.sh exits with code 99 if the worker is not connected to cvmfs or hdfs
#   in this case, we want to retry and hopefully find a worker that is correctly connected
#
# The period of this release depends on our specific configuration of HTCondor.
#   The default is 60s, but our configuration may be different (and I can't figure it out).
if arg.periodic_release :
    job_instructions.periodic_release()

# If 'save_output' is defined on the command line
#   use the passed string as the directory to dump terminal output files
# ONLY GOOD FOR DEBUGGING
#   This *will* overload the file system if you run a full scale number of jobs
#   will trying to save all the terminal output to one directory.
if arg.save_output is not None :
    job_instructions.save_output(arg.save_output)

if arg.input_dir is not None :
    job_instructions.run_over_input_dirs(arg.input_dir, arg.files_per_job)
elif arg.refill :
    job_instructions.run_refill()
else :
    job_instructions.run_numbers(arg.start_job, arg.num_jobs)
#input directory or not

if arg.nocheck :
    job_instructions.submit()
else :
    job_instructions.submit_interactive()
