import logging
from logging import getLoggerClass, addLevelName, setLoggerClass, NOTSET

UEVENT = logging.CRITICAL + 5


class UserEventLogger(getLoggerClass()):
    """
    Class for adding a custom event to our logging
    """

    def __init__(self, name, level=NOTSET):
        super(UserEventLogger, self).__init__(name, level)

        addLevelName(UEVENT, "UEVENT")

    def uevent(self, msg, *args, **kwargs):
        if self.isEnabledFor(UEVENT):
            self._log(UEVENT, msg, args, **kwargs)


setLoggerClass(UserEventLogger)
