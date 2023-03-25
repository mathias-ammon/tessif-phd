# tessif/write/log.py
import logging
from tessif.frused.configurations import logging_file_paths as lfps
import inspect
from timeit import default_timer as stopwatch
import functools
import os


def timings_logged(logger=None, uexp=3):
    r"""Decorater to log: caller, called and passed time. Specify logging
    object with *logger* and resolution as in 1e-*uexp* seconds.

    Parameters
    ----------
    logger : :class:`logging.Logger`,
        Logger object to use for logging. Usually the one gotten by
        ``logger.getLogger(__name__)``. If None provided, decorated
        function's module is used. (As in ``getLogger(func.__module__)``)
    uexp : int, default=3
       Time resolution modifier as in ``1e-uexp`` seconds. Default leads to
       a resolution in milliseconds.
    """

    def decorated(func):
        @functools.wraps(func)
        def with_logging(*args, **kwargs):
            # Start time measurement
            start = stopwatch()
            # Credit to https://stackoverflow.com/a/53490973
            # Figure out caller using the previous frame:
            prev_frame = inspect.currentframe().f_back
            if "self" in prev_frame.f_locals:
                caller = prev_frame.f_locals["self"].__class__.__name__
            # or the module level function
            else:
                if func.__module__ == '__main__':
                    # get source file abspath
                    source_abspath = inspect.getsourcefile(func)
                    # extract module and package
                    caller_as_list = os.path.join(source_abspath.split('.py')
                                                  [0]).split(os.path.sep)[-2:]

                    caller = '{}.{}'.format(*caller_as_list)

                else:
                    caller = '{}.{}'.format(*func.__module__.split('.')[-2:])

            # called name can easiliy be accessed by just asking it :)
            called = func.__name__

            nonlocal logger
            if not logger:
                logger = logging.getLogger(func.__module__)

            logger.timings('{}.{} time stopping'. format(caller, called))

            # make the function that was decorated opreate as usual
            result = func(*args, **kwargs)

            # End logging
            logger.timings('{}.{} executed in {:.0f}e-{}s'.format(
                caller, called, (stopwatch()-start)*1*10**(uexp), uexp))
            logger.timings(40*'-')

            return result
        return with_logging
    return decorated


#: Default :func:`timings_logged` decorator
timings = timings_logged()


def add_logging_level_timings():
    """
    Logging level to report computational timings.

    Add a logging level below logging.DEBUG to not annoy any other loggers.
    Every computational milestone throughout :ref:`Tessif <api>` will be
    logged on this level.

    Logging to this level can be archived by calling ``logger.timings()``.

    Meant to be used with a :class:`filter <TimingsFilter>` to only log timing
    events for keeping the log as clean as possible.
    """

    # Add logging level below logging.DEBUG to log computational timings
    logging.TIMINGS = 8  # Define level constant
    logging.addLevelName(logging.TIMINGS, "TIMINGS")  # add to level namepsace

    # add logging.timmings('msg') function
    def timings(self, message, *args, **kws):     # define function
        if self.isEnabledFor(logging.TIMINGS):
            # Yes, logger takes its '*args' as 'args'.
            self._log(logging.TIMINGS, message, args, **kws)

    # add function to logging.Logger class for further calling
    logging.Logger.timings = timings


class TimingsFilter(logging.Filter):
    """
    Filter out everything but
    :attr:`logging.TIMINGS <add_logging_level_timings>`.
    """

    def filter(self, record):
        return (record.levelno is logging.TIMINGS)


supported_logging_levels = [
    'timings', 'debug', 'info', 'warning', 'error']
"""
Supported `logging levels
 <https://docs.python.org/3/library/logging.html#logging-levels>`_.
"""

logging_levels = {k: k for k in supported_logging_levels}
"""
Mapping tessifs `logging level
<https://docs.python.org/3/library/logging.html#logging-levels>`_ tags to
themselves for failsafe logging level accesss.
"""


def setup(
        debug=lfps['debug'],
        debug_log_logging_level=logging.DEBUG,
        # content log aka info:
        content=lfps['content'],
        content_log_logging_level=logging.INFO,
        # timings log
        timings=lfps['timings'],
        timings_log_logging_level=8,
        # log file parameters:
        log_file_format=None,
        log_file_time_format=None,
        # shell logging parameters:
        stdout_logging_level=logging.INFO,
        stdout_logging_format=None):
    """
    Convenience wrapper to configure logging behaviour.

    Parameters
    ----------
    debug : str
        Debug log file's absolute path. Change default behaviour in
        :attr:`tessif.frused.configurations.logging`.

    debug_log_file_level: int
        Debug loggers logging level. Default = logging.DEBUG.
        See https://docs.python.org/2/library/logging.html#logging-levels
        for details on logging levels.

    content : str
        Content log file's absolute path. Change default behaviour in
        :mod:`tessif.frused.paths`.

    content_log_file_level: int
        Content loggers logging level. Default: logging.INFO (20).
        See https://docs.python.org/2/library/logging.html#logging-levels
        for details on logging levels.

    timings : str
        Timings log file's absolute path. Change default behaviour in
        :mod:`tessif.frused.paths`.

    timings_log_file_level: int
        Timings loggers logging level. Default: logging.TIMINGS (8).
        See https://docs.python.org/2/library/logging.html#logging-levels
        for details on logging levels.

    log_file_format: str
        Formatting string for logged messages inside logging files.
        Default: [{levelname} at {asctime}] {msg}'
        i.e.: [TIMINGS at 1986-01-01 00:00:00]  This is a Timing log!

    log_file_time_format: str
        Formatting string for time indication in logged messages inside logging
        files. Default: '%Y-%m-%d %H:%M:%S'
        i.e: 1234-12-24 18:00:59

    stdout_logging_level: int
        Standard stream output logging level. Default: logging.INFO(20)
        See https://docs.python.org/2/library/logging.html#logging-levels
        for details on logging levels.

    stout_logging_format: str
        Formatting string for logged messages sent to stdout.
        Default: [{levelname} at {asctime}] {msg}'
        i.e.: [Info at 1986-01-01 00:00:00]  This is a very informative log!

    """
    # Add logging level below logging.Debug to log timings:
    add_logging_level_timings()

    # Get root logger
    root_logger = logging.getLogger()

    # Set logging level to the lowest (1) to let handles assign levels
    root_logger.setLevel(1)

    # File handles:
    debug_file_handle = logging.FileHandler(debug, mode='w')  # w for write
    debug_file_handle.setLevel(debug_log_logging_level)

    content_file_handle = logging.FileHandler(content, mode='w')  # w for write
    content_file_handle.setLevel(content_log_logging_level)

    timings_file_handle = logging.FileHandler(timings, mode='w')  # w for write
    timings_file_handle.setLevel(timings_log_logging_level)
    # Add filter to only allow messages between 11 and 20
    timings_file_handle.addFilter(TimingsFilter())

    # Stream handles:
    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(logging.INFO)

    # File formatters:
    if not log_file_format:  # loging msg structure
        log_file_format = '[{levelname} at {asctime}] {msg}'
    if not log_file_time_format:  # time stemp format:
        log_file_time_format = '%Y-%m-%d %H:%M:%S'
    file_formatter = logging.Formatter(
        log_file_format, datefmt=log_file_time_format, style='{')

    # Stream formatter
    if not stdout_logging_format:  # logging msg structure
        stdout_logging_format = '[{levelname} at {asctime}] {msg}'
    stdout_formatter = logging.Formatter(
        stdout_logging_format, datefmt=log_file_time_format, style='{')

    # 4.) Add formatters to handlers:
    debug_file_handle.setFormatter(file_formatter)
    content_file_handle.setFormatter(file_formatter)
    timings_file_handle.setFormatter(file_formatter)
    stdout_handler.setFormatter(stdout_formatter)

    # 5.) Add handles to root logger if not done already:
    if not root_logger.hasHandlers():
        root_logger.addHandler(debug_file_handle)
        root_logger.addHandler(content_file_handle)
        root_logger.addHandler(timings_file_handle)
        root_logger.addHandler(stdout_handler)


setup()
