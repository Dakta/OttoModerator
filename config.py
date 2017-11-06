# Import configuration from guarded file
import sys, os
from configparser import SafeConfigParser

cfg_file = SafeConfigParser()
path_to_cfg = os.path.abspath(os.path.dirname(sys.argv[0]))
path_to_cfg = os.path.join(path_to_cfg, 'ottomoderator.cfg')
cfg_file.read(path_to_cfg)

# set up logging
import logging, logging.config

# register new log level
# TRACE is even more verbose than DEBUG
setattr(logging, "TRACE", logging.DEBUG-1)
logging.addLevelName(logging.TRACE, "TRACE")

# the following are lifted from Lib/logging/__init__.py
def logging_Logger_trace(self, msg, *args, **kwargs):
    """
    Log 'msg % args' with severity 'TRACE'.
    To pass exception information, use the keyword argument exc_info with
    a true value, e.g.
    logger.info("Houston, we have a %s", "interesting problem", exc_info=1)
    """
    if self.isEnabledFor(logging.TRACE):
        self._log(logging.TRACE, msg, args, **kwargs)

def logging_LoggerAdapter_trace(self, msg, *args, **kwargs):
    """
    Delegate an info call to the underlying logger.
    """
    self.log(logging.TRACE, msg, *args, **kwargs)

def logging_trace(msg, *args, **kwargs):
    """
    Log a message with severity 'TRACE' on the root logger. If the logger has
    no handlers, call basicConfig() to add a console handler with a pre-defined
    format.
    """
    if len(root.handlers) == 0:
        basicConfig()
    root.info(msg, *args, **kwargs)

# attach the methods
setattr(logging, 'trace', logging_trace)
setattr(logging.Logger, 'trace', logging_Logger_trace)
setattr(logging.LoggerAdapter, 'trace', logging_LoggerAdapter_trace)

# configure from file, and we should be good
logging.config.fileConfig(path_to_cfg)
