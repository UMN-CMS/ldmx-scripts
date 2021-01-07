"""UMN HTCondor specialization for managing batch jobs"""

from umn_htcondor import utility
import htcondor #HTCondor Python API
import classad #htcondor internal data structure
import getpass #for username

def my_q(extra_filters = 'TRUE') :
    """Get the queue for the current user"""
    schedd = htcondor.Schedd()
    return schedd.xquery(utility.job_is_mine().and_(extra_filters))

def ban_machine(broken_machine) :
    """Ban a machine from being used to run your jobs.

    We assume that there is already at least one
    requirement for all of the jobs. This is a fine
    assumption since all of our jobs have the requirements
    to avoid using the zebras.

    UNTESTED

    Parameters
    ----------
    broken_machine : str
        Name of machine to ban without URL (e.g. scorpion3)
    
    Examples
    --------
    >>> import umn_htcondor.manage as manage
    >>> manage.ban_machine('scorpion43')
    """

    # need to edit each job individually because they might
    #   have different requirements
    schedd = htcondor.Schedd()
    for j in my_q() :
        schedd.edit(
            f'{j["ClusterId"]}.{j["ProcId"]}',
            'requirements',
            classad.ExprTree(j["requirements"]).and_(utility.dont_use_machine(broken_machine))
            )

def translate_job_status_enum(s) :
    """Translate status enum to human-readable status

    Parameters
    ----------
    s : int
        Job status enum
    """

    translation = {
        1 : 'I', # Idle
        2 : 'R', # Running
        3 : 'E', # Evicting (removing)
        4 : 'C', # Completed
        5 : 'H', # Held
        6 : 'T', # Transferring output
        7 : 'S'  # Suspended
        }

    if s in translation :
        return translation[s]
    else :
        return str(s)

def print_q(extra_filters = True) :
    """Print the job listing for the current user

    Specialization of printing for what we care about.
    ClusterId, ProcId, and the last argument given to the executable (either input files or run number)
    """

    print(f'Cluster.Proc : St : HH:MM:SS : Input')
    for j in my_q(extra_filters) :
        job_status = translate_job_status_enum(j['JobStatus'])
        run_time = j['ServerTime'] - j['LastMatchTime'] #in s
        hours = run_time // 3600
        run_time %= 3600
        minutes = run_time // 60
        seconds = run_time % 60
        print(f'{j["ClusterId"]:7}.{j["ProcId"]:<4} : {job_status:2} : {hours:02d}:{minutes:02d}:{seconds:02d} : {j["Args"].split(" ")[-1]}')

def hosts(held_only = False, running_only = False, extra_filters = True) :
    """Return the list of unique hosts that are being used.

    We remove the slot numbers in favor of a raw count,
    we remove the URL of all the machines '.spa.umn.edu',
    and we add a prefix to tell the user if the machine produced
    a HELD job or if the machine is a RUN job.

    Returns
    -------
        dict : hosts to counts of jobs held from them or running on them

    Examples
    --------
    To get all the hosts that are listed for either running or held jobs, simply run
    >>> manage.hosts()

    To get the hosts only for running jobs
    >>> manage.hosts(running_only = True)

    To get the hosts only for held jobs
    >>> manage.hosts(held_only = True)
    """

    if held_only :
        filters = utility.job_status_is_held()
    elif running_only :
        filters = utility.job_status_is_running()
    else :
        filters = utility.job_status_is_held().and_(utility.job_status_is_running())

    filters = filters.and_(extra_filters)

    uniq_hosts = dict()
    for j in my_q(filters) :
        if j["JobStatus"] == htcondor.JobStatus.RUNNING :
            the_host = j["RemoteHost"]
        else :
            the_host = j["LastRemoteHost"]

        the_host = utility.get_umn_host_name(the_host)

        if the_host not in uniq_hosts :
            uniq_hosts[the_host] = 0

        uniq_hosts[the_host] += 1
    #end loop over query

    return uniq_hosts

def _my_act(action, constraint) :
    """Perform a action on a set of jobs

    Parameters
    ----------
    action : htcondor.JobAction
        The action that should be done on all matching jobs
    constraint : classad.ExprTree
        Constraint applied to determine set of jobs to apply action to
    """

    schedd = htcondor.Schedd()
    schedd.act(action, utility.job_is_mine().and_(constraint), reason=f'{getpass.getuser()} asked me to.')

def rm_all() :
    """Remove all of your jobs from the queue."""
    _my_act(htcondor.JobAction.Remove, True)

def rm_held() :
    _my_act(htcondor.JobAction.Remove, utility.job_status_is_held())

def release_me() :
    _my_act(htcondor.JobAction.Release, True)

