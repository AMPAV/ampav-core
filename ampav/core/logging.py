import logging


LOG_FORMAT = "%(asctime)s [%(levelname)-8s] (%(filename)s:%(lineno)d:%(process)d) %(message)s"

class ListLoggingHandler(logging.Handler):
    """
    Docstring for ListLoggingHandler
    """
    def __init__(self, log: list, format: str | logging.Formatter=None):
        """
        Initialize the List Logging Handler

        :param log: List to append new logging messages to
        :type log: list

        :param format: Either a format string or a preconfigured formatter        
        """
        super().__init__()
        self.log = log

        if format is None:
            self.setFormatter(logging.Formatter(LOG_FORMAT))
        else:
            if isinstance(format, logging.Formatter):
                self.setFormatter(format)
            else:
                self.setFormatter(logging.Formatter(format))



    def emit(self, record):
        self.log.append(self.format(record))

