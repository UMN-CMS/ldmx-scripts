"""Writing jobs for ldmx Condor batch submission

This python script is intended to be used with the running script 'run_fire.sh' in
this current directory.
"""

import os,sys
import argparse

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

# required arg
parser.add_argument("sub_file_name",type=str,help="Name of submission file that we should write to.")
parser.add_argument("-c","--config",required=True,type=str,help="Config script to run.")
parser.add_argument("-o","--out_dir",required=True,type=str,help="Directory to copy output to.")
environment = parser.add_mutually_exclusive_group(required=True)
environment.add_argument("--env_script",type=str,default=None,help="Environment script to run before running fire.")
environment.add_argument("--ldmx_version",type=str,default=None,help="LDMX Version to pick a pre-made environment script.")
how_many_jobs = parser.add_mutually_exclusive_group(required=True)
how_many_jobs.add_argument("--input_dir",default=None,type=str,help="Directory containing input files to run over.")
how_many_jobs.add_argument("--num_jobs",type=int,default=None,help="Number of jobs to run (if not input directory given).")

# optional arg
parser.add_argument("--input_arg_name",type=str,default='--input_file',help='Name of argument that should go before the input file when passing it to the config script. Only used if running over the items in a directory.')
parser.add_argument("--run_arg_name",type=str,default='--run_number',help='Name of argument that should go before the run number when passing it to the config script. Only used if NOT running over items in a directory.')
parser.add_argument("--config_args",type=str,default='',help="Extra arguments to be passed to the configuration script.")
parser.add_argument("--start_job",type=int,default=0,help="Starting number to use when run numbers. Only used if NOT running over items in a directory.")

# rarely-used optional args
parser.add_argument("-t","--test",action='store_true',dest='test',help="Attach terminal output of worker nodes to files for later viewing. ONLY GOOD FOR DEBUGGING. This will overload the filesystem if you use it on large batches.")
parser.add_argument("--nonice",action='store_true',dest="nonice",help="Do not run this at nice priority.")
parser.add_argument("--run_script",type=str,help="Script to run jobs on worker nodes with.",default='%s/run_fire.sh'%os.path.dirname(os.path.realpath(__file__)))
parser.add_argument("--scratch_root",type=str,help="Directory to create any working directories inside of.",default='/export/scratch/user/%s'%os.environ['USER'])
parser.add_argument("--sleep",type=int,help="Time in seconds to sleep before starting the next job.",default=60)

arg = parser.parse_args()

# make the output directory
full_out_dir_path = os.path.realpath(arg.out_dir)
if not os.path.exists(full_out_dir_path):
    os.makedirs(full_out_dir_path)

if not os.path.exists(full_out_dir_path):
    raise Exception('Unable to create output directory "%s"'%full_out_dir_path)

full_config_path = os.path.realpath(arg.config)
if not os.path.exists(full_config_path) :
    raise Exception('Config script "%s" does not exist.'%full_config_path)

if 'hdfs' not in full_config_path :
    print(' WARN You are running a config script that is *not* in /hdfs/cms/%s/.'%os.environ['USER'])

if arg.env_script is not None :
    env_script = os.path.realpath(arg.env_script)
else :
    env_script = "/local/cms/user/%s/ldmx/stable-installs/%s/setup.sh"%(os.environ['USER'],arg.ldmx_version)

if not os.path.exists(env_script) :
    raise Exception('Environment script "%s" does not exist.'%env_script)

sub_file_template="""# Condor Submission File
# Header for Jobs, defines global variables for use in this condor submission
#   anything defined here will be defined for the rest of this submission file
#   they can be re-defined and then the new value would be used for any later 'queue' commands

# These variables are general condor variables that are helpful for us
universe     = vanilla
requirements = Arch==\"X86_64\" && (Machine  !=  \"zebra01.spa.umn.edu\") && (Machine  !=  \"zebra02.spa.umn.edu\") && (Machine  !=  \"zebra03.spa.umn.edu\") && (Machine  !=  \"zebra04.spa.umn.edu\") && (Machine  !=  \"caffeine.spa.umn.edu\")
+CondorGroup = \"cmsfarm\"

# How much memory does this job require?
#   This is somewhat hard to determine since one does not normally track memory usage of one's programs.
#   4 Gb of RAM is a high upper limit, so this probably mean that less jobs will run in parallel, BUT
#   it helps make sure no jobs slow down due to low amount of available memory.
request_memory = 4 Gb

# This line keeps any jobs in a 'hold' state return a failure exit status
#   If you are developing a new executable (run script), this might need to be removed
#   until you get your exit statuses defined properly
on_exit_hold = (ExitCode != 0)

# This line tells condor whether we should be 'nice' or not.
#   Niceness is a way for condor to help determine how 'urgent' this job is
#   Please default to alwasy being nice
nice_user = {nice}

# Now our job specific information
#   'executable' is required by condor and that variable name cannot be changed
#   the other variable names are ours and can be changed and used in the rest of this file
executable    = {executable}
env_script    = {env_script}
scratch_root  = {scratch_root}
config_script = {config}
output_dir    = {out_dir}

# This is the number of seconds to pause between starting jobs
#   It is helpful to have some lag time so that transferring large files can happen
#   without overloading the file system
next_job_start_delay = {sleep}
{run_number_calc}
# Finally, we define the arguments to the executable we defined earlier
#   Notice that we can use the variables we have defined earlier in this argument list
#   Condor will make the substitutions before starting the job
arguments = {arguments}
{terminal_output}
# Submit the Jobs
#   Now we actually submit the jobs.
#   The 'queue' command can do several things and this is where Condor handles the variables defined about it.
#   Look at the Condor documentation for all the details about how to write a helpful 'queue' command.
{queue_command}
"""

run_number_calculation="""
# We will be using a run_number in the argument list, so we define it here
#   as a special variable that is a shift away from the Process ID.
#   Process is a condor defined variable that starts at 0 and increments up for each
#   job submitted. Here we use it to define sequential run numbers.
run_number_calculation = $(Process) + {start_job}
run_number = $INT(run_number_calculation)
"""

# This needs to match the correct order of the arguments in the run_fire.sh script
#   The input file and any extra config arguments are optional and come after the
#   three required arguments
arguments = '$(scratch_root)/$(Cluster)-$(Process) $(env_script) $(config_script) $(output_dir)'

queue_command = ''

if arg.input_dir is not None :
    run_number_calculation = "" #no need for run number when running over input files
    arguments += ' ' + arg.input_arg_name + ' $(input)'
    # submitting the whole directory
    full_input_dir = os.path.realpath(arg.input_dir)
    if 'hdfs' not in full_input_dir :
        print(' WARN You are running jobs over files in a directory *not* in /hdfs/cms/%s/.'%os.environ['USER'])
    queue_command += 'queue input matching files %s/*\n'%(full_input_dir)
else :
    run_number_calculation = run_number_calculation.format(start_job = arg.start_job)
    arguments += ' ' + arg.run_arg_name + ' $(run_number)'
    # submitting a range of run numbers
    queue_command += 'queue %d \n'%(arg.num_jobs)

arguments += arg.config_args

terminal_output = """
# Print any terminal messages that come up during the job to the file below
output = $(output_dir)/$(Cluster)-$(Process).out
error  = $(output_dir)/$(Cluster)-$(Process).out
"""

if not arg.test :
    terminal_output = ""

with open(arg.sub_file_name,'w') as submission_file :
    submission_file.write(sub_file_template.format(
          executable=os.path.realpath(arg.run_script),
          nice=str(not arg.nonice),
          env_script = env_script,
          scratch_root = arg.scratch_root,
          config = full_config_path,
          out_dir = full_out_dir_path,
          sleep = arg.sleep,
          arguments = arguments,
          run_number_calc = run_number_calculation,
          terminal_output = terminal_output,
          queue_command = queue_command
          ))
