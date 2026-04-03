import logging


LOG_FORMAT = "%(asctime)s [%(levelname)-8s] (%(filename)s:%(lineno)d:%(process)d) %(message)s"

class ListLoggingHandler(logging.Handler):
    """
    Docstring for ListLoggingHandler
    """
    def __init__(self, log: list):
        """
        Initialize the List Logging Handler

        :param log: List to append new logging messages to
        :type log: list
        """
        self.log = log

    def emit(self, record):
        self.log.append(self.format(record))

