import logging
import logging.handlers
import os


class clog(object):
    """
    Class: clog.
     Common used for logging.
    """

    def __init__(self):
        """
        Initialisation of logging.
        """
        self._created = False
        self._loglevel = logging.INFO
        self._fileonly = ""
        self._pathonly = ""

    def create_logfile(
        self,
        logfilepath="./default_logfile.log",
        loglevel=logging.INFO,
        loggertag="default",
    ):
        """
        Create logfile with default-values (overwrite-able).
        """
        self._logfilepath = logfilepath
        self._loglevel = loglevel
        self._loggertag = loggertag
        self._pathonly = ""
        self._fileonly = ""
        (path, filename) = os.path.split(logfilepath)
        if len(path) > 0:
            self._pathonly = os.path.normcase(path)
        if len(filename) > 0:
            self._fileonly = filename

        try:
            self._handler = logging.handlers.RotatingFileHandler(
                self._logfilepath, maxBytes=1000000
            )
            _frm = logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s", "%d.%m.%Y %H:%M:%S"
            )
            self._handler.setFormatter(_frm)
            self._logger = logging.getLogger(self._loggertag)
            self._logger.addHandler(self._handler)
            self._logger.setLevel(self._loglevel)
            self._created = True
            return self._logger
        except:
            raise EnvironmentError(
                "clog.create_logfile();Error; could not create logging"
            )

    def critical(self, logmessage):
        """
        Log in critical error-level.
        """
        if not self._created:
            raise EnvironmentError(
                "clog.critical();Error; logging not created, call clog.create_logfile() at first"
            )
        self._logger.critical(logmessage)

    def error(self, logmessage):
        """
        Log in standard error-level.
        """
        if not self._created:
            raise EnvironmentError(
                "clog.error();Error; logging not created, call clog.create_logfile() at first"
            )
        self._logger.error(logmessage)

    def warning(self, logmessage):
        """
        Log in warning-level.
        """
        if not self._created:
            raise EnvironmentError(
                "clog.warning();Error; logging not created, call clog.create_logfile() at first"
            )
        self._logger.warning(logmessage)

    def info(self, logmessage):
        """
        Log in info-level.
        """
        if not self._created:
            raise EnvironmentError(
                "clog.info();Error; logging not created, call clog.create_logfile() at first"
            )
        self._logger.info(logmessage)

    def debug(self, logmessage):
        """
        Log in debug-level.
        """
        if not self._created:
            raise EnvironmentError(
                "clog.debug();Error; logging not created, call clog.create_logfile() at first"
            )
        self._logger.debug(logmessage)

    def logfilepathname(self, logfilepath=None):
        """
        returns the currently defined 'logpath'.
         Value is set in configuration-file.
        """
        if logfilepath != None:
            self._logfilepath = logfilepath
        return self._logfilepath

    def logfilename(self, logfilename=None):
        """
        returns the currently defined 'logfilename'.
         Value is set in configuration-file.
        """
        if logfilename != None:
            self._fileonly = logfilename
            self._logfilepath = os.path.normcase(
                os.path.join(self._pathonly, self._fileonly)
            )
        return self._fileonly

    def logpathname(self, logpathname=None):
        """
        returns the currently defined 'logfilename joined with 'logpath'.
         Values are set in configuration-file.
        """
        if logpathname != None:
            self._pathonly = logpathname
            self._logfilepath = os.path.normcase(
                os.path.join(self._pathonly, self._fileonly)
            )
        return self._pathonly

    def loglevel(self, loglevel=None):
        """
        returns the currently defined 'loglevel' as defined in logging.py.
         Value is set in configuration-file.
        """
        if loglevel != None:
            tmp_loglevel = loglevel.upper()
            # check first possible parameters
            if tmp_loglevel in ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"):
                if tmp_loglevel in ("CRITICAL"):
                    loglevel = logging.CRITICAL
                if tmp_loglevel in ("ERROR"):
                    loglevel = logging.ERROR
                if tmp_loglevel in ("WARNING"):
                    loglevel = logging.WARNING
                if tmp_loglevel in ("INFO"):
                    loglevel = logging.INFO
                if tmp_loglevel in ("DEBUG"):
                    loglevel = logging.DEBUG
                self._loglevel = loglevel
            else:
                self._loglevel = logging.INFO
        # zs#test# print("loglevel:{0}".format(logging.getLevelName(self._loglevel)))
        return self._loglevel
