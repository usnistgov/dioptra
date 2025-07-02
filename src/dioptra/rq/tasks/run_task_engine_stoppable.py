# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode
import multiprocessing as mp
import signal
from typing import Any, Mapping, MutableMapping

import structlog

from dioptra.task_engine.task_engine import request_stop, run_experiment

# Which endpoint to poll
_POLL_URL = "http://dioptra-deployment-restapi:5000/something"


# Web server endpoint poll interval, in seconds
_POLL_INTERVAL = 3


def _get_logger() -> Any:
    """
    Get a logger for this module.

    Returns:
        A logger object
    """
    return structlog.get_logger(__name__)


def run_experiment_stoppable(
    experiment_desc: Mapping[str, Any], global_parameters: MutableMapping[str, Any]
) -> bool:
    """
    Run an experiment via the task engine.  This implementation runs it in a
    sub-process.  The parent process will poll an endpoint for a shutdown
    instruction which will cause us to stop the experiment early.

    Args:
        experiment_desc: A declarative experiment description, as a mapping
        global_parameters: Global parameters for this run, as a mapping from
            parameter name to value

    Returns:
        True if the process was stopped prematurely; False if not
    """
    child_process = mp.Process(
        target=_run_experiment_child_process, args=(experiment_desc, global_parameters)
    )

    child_process.start()

    was_stopped = _monitor_process(child_process)

    child_process.close()

    return was_stopped


def _run_experiment_child_process(
    experiment_desc: Mapping[str, Any], global_parameters: MutableMapping[str, Any]
) -> None:
    """
    Simple wrapper around run_experiment() which arranges for SIGTERM to
    request graceful termination of the experiment.

    Args:
        experiment_desc: A declarative experiment description, as a mapping
        global_parameters: Global parameters for this run, as a mapping from
            parameter name to value
    """

    signal.signal(signal.SIGTERM, lambda *args: request_stop())

    run_experiment(experiment_desc, global_parameters)


def _monitor_process(child_process: mp.Process) -> bool:
    """
    Watch the given child process while polling for a shutdown request.
    If shutdown is requested, shut down the child process early.

    This function blocks until the child process terminates.

    Args:
        child_process: The child process to watch

    Returns:
        True if the process was stopped prematurely; False if not
    """
    log = _get_logger()
    log.debug("Monitoring task engine process: %d", child_process.pid)

    should_stop = False
    while child_process.is_alive():
        should_stop = _should_stop()

        if should_stop:
            log.warning("Attempting to stop pid: %d", child_process.pid)
            # Send a SIGTERM to attempt a graceful shutdown
            child_process.terminate()

            # Wait one poll interval to see if it stops.  If not, forcibly
            # kill it.
            child_process.join(_POLL_INTERVAL)

            # Docs describe checking .exitcode, not .is_alive().
            if child_process.exitcode is None:
                log.warning(
                    "Graceful shutdown failed; killing pid: %d", child_process.pid
                )
                child_process.kill()
                child_process.join()

        else:
            # Wait until next poll
            child_process.join(_POLL_INTERVAL)

    return should_stop


def _should_stop() -> bool:
    """
    Determine whether the current experiment should be stopped.

    Returns:
        True if it should be stopped; False if not
    """
    # resp = requests.get(_POLL_URL)
    # if resp.ok:
    #     # Depends on what the endpoint returns
    #     value = cast(bool, resp.json())
    #
    # else:
    #     log.warning("Polling endpoint returned http status: %d", resp.status_code)
    #     value = False

    value = False
    return value
