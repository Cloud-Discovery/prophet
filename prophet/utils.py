# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2017 Prophet Tech (Shanghai) Ltd.
#
# Authors: Zheng Wei <zhengwei@prophetech.cn>
# Authors: Ray <sunqi@prophetech.cn>
#
# Copyright (c) 2017. This file is confidential and proprietary.
# All Rights Reserved, Prophet Tech (Shanghai) Ltd(http://www.prophetech.cn).

"""Common method module"""

import logging
import calendar
import errno
import functools
import logging
import os
import platform
import random
import sys
import shlex
import signal
import subprocess
import time
from datetime import datetime

# Default path for logs
DEFAULT_PATH = "logs"

# Default log format
LOG_FORMAT = "%(asctime)s %(process)s %(levelname)s [-] %(message)s"


class ProcessExecutionError(Exception):
    def __init__(self, stdout=None, stderr=None, exit_code=None,
                 cmd=None, description=None):
        self.exit_code = exit_code
        self.stderr = stderr
        self.stdout = stdout
        self.cmd = cmd
        self.description = description

        if description is None:
            description = "Unexpected error while running command."

        if exit_code is None:
            exit_code = '-'
        message = ('%(description)s\n'
                   'Command: %(cmd)s\n'
                   'Exit code: %(exit_code)s\n'
                   'Stdout: %(stdout)r\n'
                   'Stderr: %(stderr)r') % {'description': description,
                                            'cmd': cmd,
                                            'exit_code': exit_code,
                                            'stdout': stdout,
                                            'stderr': stderr}
        super(ProcessExecutionError, self).__init__(message)


class LogErrors(object):
    """Enumerations that affect if stdout and stderr are logged on error.

    .. versionadded:: 2.7
    """

    #: No logging on errors
    DEFAULT = 0

    #: Log an error on **each** occurence of an error.
    ALL = 1

    #: Log an error on the last attempt that errored **only**
    FINAL = 2

    def __init__(self, code):
        self._code = code

    def __repr__(self):
        return self._code


# Retain these aliases for a number of releases
LOG_ALL_ERRORS = LogErrors.ALL
LOG_FINAL_ERROR = LogErrors.FINAL
LOG_DEFAULT_ERROR = LogErrors.DEFAULT


def is_python_3():
    return platform.python_version().startswith('3.')


def _subprocess_setup(on_preexec_fn):
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    if on_preexec_fn:
        on_preexec_fn()


def execute(*cmd, **kwargs):
    """Helper method to shell out and execute a command through subprocess.

    Allows optional retry.

    :param cmd:             Passed to subprocess.Popen.
    :type cmd:              string
    :param cwd:             Set the current working directory
    :type cwd:              string
    :param process_input:   Send to opened process.
    :type process_input:    string
    :param env_variables:   Environment variables and their values that
                            will be set for the process.
    :type env_variables:    dict
    :param check_exit_code: Single bool, int, or list of allowed exit
                            codes.  Defaults to [0].  Raise
                            :class:`ProcessExecutionError` unless
                            program exits with one of these code.
    :type check_exit_code:  boolean, int, or [int]
    :param delay_on_retry:  True | False. Defaults to True. If set to True,
                            wait a short amount of time before retrying.
    :type delay_on_retry:   boolean
    :param attempts:        How many times to retry cmd.
    :type attempts:         int
    :param run_as_root:     True | False. Defaults to False. If set to
                            True, the command is prefixed by the command
                            specified in the root_helper kwarg.
    :type run_as_root:      boolean
    :param root_helper:     command to prefix to commands called with
                            run_as_root=True
    :type root_helper:      string
    :param shell:           whether or not there should be a shell used to
                            execute this command. Defaults to false.
    :type shell:            boolean
    :param loglevel:        log level for execute commands.
    :type loglevel:         int.  (Should be logging.DEBUG or logging.INFO)
    :param log_errors:      Should stdout and stderr be logged on error?
                            Possible values are
                            :py:attr:`~.LogErrors.DEFAULT`,
                            :py:attr:`~.LogErrors.FINAL`, or
                            :py:attr:`~.LogErrors.ALL`. Note that the
                            values :py:attr:`~.LogErrors.FINAL` and
                            :py:attr:`~.LogErrors.ALL`
                            are **only** relevant when multiple attempts of
                            command execution are requested using the
                            ``attempts`` parameter.
    :type log_errors:       :py:class:`~.LogErrors`
    :param binary:          On Python 3, return stdout and stderr as bytes
                            if binary is True, as Unicode otherwise.
    :type binary:           boolean
    :param on_execute:      This function will be called upon process
                            creation with the object as a argument.
                            The Purpose of this is to allow the caller of
                            `processutils.execute` to track process
                            creation asynchronously.
    :type on_execute:       function(:class:`subprocess.Popen`)
    :param on_completion:   This function will be called upon process
                            completion with the object as a argument. The
                            Purpose of this is to allow the caller of
                            `processutils.execute` to track process
                            completion asynchronously.
    :type on_completion:    function(:class:`subprocess.Popen`)
    :param preexec_fn:      This function will be called
                            in the child process just before the child
                            is executed. WARNING: On windows, we silently
                            drop this preexec_fn as it is not supported by
                            subprocess.Popen on windows (throws a
                            ValueError)
    :type preexec_fn:       function()
    :returns:               (stdout, stderr) from process execution
    :raises:                :class:`UnknownArgumentError` on
                            receiving unknown arguments
    :raises:                :class:`ProcessExecutionError`
    :raises:                :class:`OSError`

    .. versionchanged:: 1.5
       Added *cwd* optional parameter.

    .. versionchanged:: 1.9
       Added *binary* optional parameter. On Python 3, *stdout* and
       *stdout* are now returned as Unicode strings by default, or bytes
       if *binary* is true.

    .. versionchanged:: 2.1
       Added *on_execute* and *on_completion* optional parameters.

    .. versionchanged:: 2.3
       Added *preexec_fn* optional parameter.
    """

    cwd = kwargs.pop('cwd', None)
    process_input = kwargs.pop('process_input', None)
    env_variables = kwargs.pop('env_variables', None)
    check_exit_code = kwargs.pop('check_exit_code', [0])
    ignore_exit_code = False
    delay_on_retry = kwargs.pop('delay_on_retry', True)
    attempts = kwargs.pop('attempts', 1)
    run_as_root = kwargs.pop('run_as_root', False)
    root_helper = kwargs.pop('root_helper', '')
    shell = kwargs.pop('shell', False)
    call = kwargs.pop('call', False)  # noqa: F841
    loglevel = kwargs.pop('loglevel', logging.DEBUG)  # noqa: F841
    log_errors = kwargs.pop('log_errors', None)
    if log_errors is None:
        log_errors = LogErrors.DEFAULT
    binary = kwargs.pop('binary', False)
    on_execute = kwargs.pop('on_execute', None)
    on_completion = kwargs.pop('on_completion', None)
    preexec_fn = kwargs.pop('preexec_fn', None)

    if isinstance(check_exit_code, bool):
        ignore_exit_code = not check_exit_code
        check_exit_code = [0]
    elif isinstance(check_exit_code, int):
        check_exit_code = [check_exit_code]

    if kwargs:
        raise Exception('Got unknown keyword args: %r' % kwargs)

    if isinstance(log_errors, int):
        log_errors = LogErrors(log_errors)
    if not isinstance(log_errors, LogErrors):
        raise Exception('Got invalid arg log_errors: %r' % log_errors)

    if run_as_root and hasattr(os, 'geteuid') and os.geteuid() != 0:
        if not root_helper:
            raise Exception('Command requested root, but did not '
                            'specify a root helper.')
        if shell:
            # root helper has to be injected into the command string
            cmd = [' '.join((root_helper, cmd[0]))] + list(cmd[1:])
        else:
            # root helper has to be tokenized into argument list
            cmd = shlex.split(root_helper) + list(cmd)

    cmd = [str(c) for c in cmd]
    sanitized_cmd = ' '.join(cmd)

    start_time = time.time()
    while attempts > 0:
        attempts -= 1

        try:
            logging.debug('Running cmd (subprocess): %s', sanitized_cmd)
            _PIPE = subprocess.PIPE  # pylint: disable=E1101

            if os.name == 'nt':
                on_preexec_fn = None
                close_fds = False
            else:
                on_preexec_fn = functools.partial(_subprocess_setup,
                                                  preexec_fn)
                close_fds = True

            obj = subprocess.Popen(cmd,
                                   stdin=_PIPE,
                                   stdout=_PIPE,
                                   stderr=_PIPE,
                                   close_fds=close_fds,
                                   preexec_fn=on_preexec_fn,
                                   shell=shell,
                                   cwd=cwd,
                                   env=env_variables)

            if on_execute:
                on_execute(obj)

            try:
                result = obj.communicate(process_input)

                obj.stdin.close()  # pylint: disable=E1101
                _returncode = obj.returncode  # pylint: disable=E1101
                logging.info('CMD "%s" returned: %s in %0.3fs',
                             sanitized_cmd, _returncode,
                             time.time() - start_time)
            finally:
                if on_completion:
                    on_completion(obj)

            if not ignore_exit_code and _returncode not in check_exit_code:
                (stdout, stderr) = result
                if is_python_3():
                    stdout = os.fsdecode(stdout)
                    stderr = os.fsdecode(stderr)
                sanitized_stdout = stdout
                sanitized_stderr = stderr
                raise ProcessExecutionError(exit_code=_returncode,
                                            stdout=sanitized_stdout,
                                            stderr=sanitized_stderr,
                                            cmd=sanitized_cmd)
            if is_python_3() and not binary and result is not None:
                (stdout, stderr) = result
                # Decode from the locale using using the surrogateescape
                # error handler (decoding cannot fail)
                stdout = os.fsdecode(stdout)
                stderr = os.fsdecode(stderr)
                return (stdout, stderr)
            else:
                return result

        except (ProcessExecutionError, OSError) as err:
            # if we want to always log the errors or if this is
            # the final attempt that failed and we want to log that.
            if log_errors == LOG_ALL_ERRORS or (
                    log_errors == LOG_FINAL_ERROR and not attempts):
                if isinstance(err, ProcessExecutionError):
                    format = "%(desc)r\ncommand: %(cmd)r\n" +\
                             "exit code: %(code)r\nstdout: %(stdout)r\n" +\
                             "stderr: %(stderr)r"
                    logging.info(format, {"desc": err.description,
                                          "cmd": err.cmd,
                                          "code": err.exit_code,
                                          "stdout": err.stdout,
                                          "stderr": err.stderr})
                else:
                    format = "Got an OSError\ncommand: " +\
                             "%(cmd)r\nerrno: %(errno)r"
                    logging.info(format, {"cmd": sanitized_cmd,
                                          "errno": err.errno})

            if not attempts:
                logging.info("%r failed. Not Retrying.", sanitized_cmd)
                raise
            else:
                logging.info("%r failed. Retrying.", sanitized_cmd)
                if delay_on_retry:
                    time.sleep(random.randint(20, 200) / 100.0)
        finally:
            time.sleep(0)


def datetime_to_timestamp(datetime_obj):
    """Convert datetime object to timestamp

    :param datetime_obj: <datetime.datetime>
    :return: a timestamp
    """
    if datetime_obj is not None:
        time_stamp = float(calendar.timegm(datetime_obj.utctimetuple()) * 1000)
        return time_stamp


def timestamp_to_datetime(timestamp_obj):
    """Convert timestamp to datetime object

    :param timestamp_obj: <int>
    :return: a datetime object
    """
    if timestamp_obj is not None:
        date_ref = datetime.utcfromtimestamp(float(timestamp_obj / 1000))
        return date_ref


def make_return(err):
    if hasattr(err, "code") is False:
        err.code = 500
    return make_response(jsonify({"message": _(err.message)}), err.code)


def current_dir():
    return os.path.normpath(os.path.join(
        os.path.abspath(sys.argv[0]), os.pardir))


def mkdir_p(path):
    """Create a mkdir -p method"""
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def init_logging(debug=False, verbose=True,
                 log_file=None, log_path=None):
    """Initilize logging for common usage

    By default, log will save at logs dir under current running path.
    """
    logger = logging.getLogger()
    log_level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(log_level)

    # Set console handler
    if verbose:
        console = logging.StreamHandler()
        console.setLevel(log_level)
        console.setFormatter(logging.Formatter(fmt=LOG_FORMAT))
        logger.addHandler(console)
    else:
        # NOTE(Ray): if verbose not given disable console output, this
        # is a tricky way to implement
        logger.handlers = []

    if log_file:
        if not log_path:
            log_path = DEFAULT_PATH

        if not os.path.exists(log_path):
            os.makedirs(log_path)

        log_path = os.path.join(log_path, log_file)

        fileout = logging.FileHandler(log_path, "a")
        fileout.setLevel(log_level)
        fileout.setFormatter(logging.Formatter(fmt=LOG_FORMAT))
        logger.addHandler(fileout)
