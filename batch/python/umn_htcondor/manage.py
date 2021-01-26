"""UMN HTCondor specialization for managing batch jobs"""

from umn_htcondor import utility
import htcondor #HTCondor Python API
import classad #htcondor internal data structure
import getpass #for username
import sys #for sys.stdout
import time #for sleep
import glob #iterating through directory

def _my_q(extra_filters = True) :
    """Get the queue for the current user

    This is meant to be an internal function,
    and returns an iterator that can be used
    in loops. This is the suggested method when potentially
    looking through long lists of jobs or a list of jobs
    that has large descriptions.

    Parameters
    ----------
    extra_filters : classad.ExprTree, optional
        Any extra filters to not list when querying the batch system

    Returns
    -------
        QueryIterator : Iterator to loop through list of jobs passing filters
    """
    schedd = htcondor.Schedd()
    return schedd.xquery(utility.job_is_mine().and_(extra_filters))

def _my_act(action, constraint) :
    """Perform a action on a set of jobs that are owned by the current user

    Parameters
    ----------
    action : htcondor.JobAction
        The action that should be done on all matching jobs
    constraint : classad.ExprTree
        Constraint applied to determine set of jobs to apply action to

    Returns
    -------
        classad.ClassAd describing number of jobs changed
    """

    schedd = htcondor.Schedd()
    return schedd.act(action, utility.job_is_mine().and_(constraint), 
        reason=f'{getpass.getuser()} asked me to.')

def ban_machine(broken_machine) :
    """Ban a machine from being used to run your jobs.

    We assume that there is already at least one
    requirement for all of the jobs. This is a fine
    assumption since all of our jobs have the requirements
    to avoid using the zebras.

    Parameters
    ----------
    broken_machine : str
        Name of machine to ban without URL (e.g. scorpion3)
    
    Examples
    --------
    >>> from umn_htcondor as manage
    >>> manage.ban_machine('scorpion43')
    """

    # need to edit each job individually because they might
    #   have different requirements
    schedd = htcondor.Schedd()
    for j in _my_q() :
        edit_result = schedd.edit(
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

def print_q(extra_filters = True, o = sys.stdout) :
    """Print the job listing for the current user

    Specialization of printing for what we care about.
    ClusterId, ProcId, Status, RunTime, and 
    the last argument given to the executable (either last input file or run number)

    Parameters
    ----------
    extra_filters : classad.ExprTree, optional
        Can do more filtering on what you want to see (default: True)
    o : file
        File to write to (default: sys.stdout)

    Examples
    --------
    Just see your entire queue
    >>> manage.print_q()

    Only see the jobs that are currently running
    >>> manage.print_q(utility.job_status_is_running())

    Write your queue to a file.
    >>> with open('queue.log','w') as queue_log :
    ...     manage.print_q(extra_filters = True, o = queue_log)
    """

    o.write(f'Cluster.Proc : St : HH:MM:SS : Input\n')
    for j in _my_q(extra_filters) :
        job_status = translate_job_status_enum(j['JobStatus'])

        if 'EnteredCurrentStatus' in j :
            run_time = j['ServerTime'] - j['EnteredCurrentStatus'] #in s
            hours = run_time // 3600
            run_time %= 3600
            minutes = run_time // 60
            seconds = run_time % 60
            time_str = f'{hours:02}:{minutes:02}:{seconds:02}'
        else :
            time_str = '--:--:--'

        last_arg = j["Args"].split(" ")[-1]
        if not last_arg.isdigit() :
            # last arg is file path, get basename
            last_arg = last_arg.split("/")[-1]
        o.write(f'{j["ClusterId"]:7}.{j["ProcId"]:<4} : {job_status:2} : {time_str} : {last_arg}\n')
    o.flush()

def get_q_totals() :
    """Print your current totals for idle, running, and held

    Returns
    -------
        list[int] : Returns counts in form [IDLE, RUNNING, HELD]

    Examples
    --------
    >>> [idle, run, held] = manage.get_q_totals()
    """
    
    tots = [0,0,0]
    for j in _my_q() :
        if j['JobStatus'] == htcondor.JobStatus.IDLE :
            tots[0] += 1
        elif j['JobStatus'] == htcondor.JobStatus.RUNNING :
            tots[1]  += 1
        elif j['JobStatus'] == htcondor.JobStatus.HELD :
            tots[2] += 1
    #end loop over queue

    return tots

def watch_q(refresh_period = 10) :
    """Watch your queue develop in terms of counts of idle, running, and held.

    End this function with a KeyboardInterrupt (ctrl-C).

    Parameters
    ----------
    refresh_period : int
        Time in seconds to wait between refreshing, default is 10s
    """

    sys.stdout.write(' IDLE  RUN HELD\n')
    while True :
        try:
            [tot_idle, tot_run, tot_held] = get_q_totals()
            sys.stdout.write(f' {tot_idle:4} {tot_run:4} {tot_held:4} {time.ctime()}\r')
            sys.stdout.flush()
            time.sleep(refresh_period)
        except KeyboardInterrupt:
            sys.stdout.write(f'\r {tot_idle:4} {tot_run:4} {tot_held:4} {time.ctime()}\n')
            sys.stdout.flush()
            break

def hosts(extra_filters = True) :
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
    >>> manage.hosts(utility.job_status_is_running())

    To get the hosts only for held jobs
    >>> manage.hosts(utility.job_status_is_held())
    """

    uniq_hosts = dict()
    for j in _my_q(extra_filters) :
        if 'LastRemoteHost' in j :
            the_host = j["LastRemoteHost"]
        elif 'RemoteHost' in j :
            the_host = j['RemoteHost']
        else :
            continue

        the_host = utility.get_umn_host_name(the_host)

        if the_host not in uniq_hosts :
            uniq_hosts[the_host] = 0

        uniq_hosts[the_host] += 1
    #end loop over query

    return uniq_hosts

def rm_all() :
    """Remove all of your jobs from the queue."""
    return _my_act(htcondor.JobAction.Remove, True)

def rm_held() :
    """Remove all of your jobs that are in the holding state."""
    return _my_act(htcondor.JobAction.Remove, utility.job_status_is_held())

def release_me() :
    """Release all of the jobs that you own (allow held jobs to re-try)."""
    return _my_act(htcondor.JobAction.Release, True)

def who() :
    """Print a table of usage based on user name. Summarizes numbers in IDLE, RUN, and HELD states."""
    users = dict()
    schedd = htcondor.Schedd()
    for j in schedd.xquery() :
        user = j["Owner"]
        if user not in users :
            users[user] = [0,0,0]

        status = j["JobStatus"]
        if status == htcondor.JobStatus.IDLE :
            users[user][0] += 1
        elif status == htcondor.JobStatus.RUNNING :
            users[user][1] += 1
        elif status == htcondor.JobStatus.HELD :
            users[user][2] += 1
    #end loop over all jobs

    user    = 'USER'
    idle    = 'IDLE'
    running = 'RUN'
    held    = 'HELD'
    print(f'{user:8}  {idle:4} {running:4} {held:4}')
    tots = [0,0,0]
    for user in users :
        idle    = users[user][0]
        running = users[user][1]
        held    = users[user][2]
        print(f'{user:8}  {idle:4d} {running:4d} {held:4d}')
        tots[0] += idle
        tots[1] += running
        tots[2] += held

    user    = 'TOTAL'
    idle    = tots[0]
    running = tots[1]
    held    = tots[2]
    print(f'{user:8}  {idle:4d} {running:4d} {held:4d}')

def why_held() :
    """Print list of exit codes on why jobs were held."""

    codes = []
    for j in _my_q(utility.job_status_is_held()) :
        c = j["HoldReasonSubCode"]
        if c not in codes: codes.append(c)

    return codes

def check_event_files(directory) :                                                                                                 
    """Sometimes batch files are only partially completed.

    This checks if a root file needs to be 'recovered', implying
    that it was only partially completed when copied over to the
    end point.
    """

    bad_files = []
    for f in glob.iglob(f'{directory}/**', recursive=False) :
        if not f.endswith('.root') : continue
        rf = ROOT.TFile.Open(f)
        print(f,end='...',flush=True)
        if rf.TestBit(ROOT.TFile.EStatusBits.kRecovered) :
            print('bad')
            bad_files.append(f)
        else :
            print('good')
    return bad_files
