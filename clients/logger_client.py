import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


class LoggerClient:
    """
    Logger client to log messages to a file
    """

    def __init__(self, logger_name: str, cfg: dict = {}, level: Optional[int] = logging.INFO):
        """
        Initialize the logger client.

        :param logger_name: name of the logger
        :param cfg: A configuration dictionary containing config for logger.
        :param level: logging level, defaults to logging.INFO
        """
        self.logger = logging.getLogger(logger_name)
        self.cfg = cfg

        BASE_LOG_PATH = self.cfg['logging']['log_path']

        if not os.path.exists(BASE_LOG_PATH):
            try:
                os.makedirs(BASE_LOG_PATH)
            except FileExistsError:
                # the dir already exists
                # put code handing this case here
                pass

        file_name = self.cfg['logging']['log_file']
        file_location = os.path.join(BASE_LOG_PATH, file_name)

        with open(file_location, "a+"):
            pass

        log_file_format = self.cfg['logging']['log_format']

        # set logging level
        self.logger.setLevel(logging.INFO)

        # create a rotating file handler to log messages to a file
        exp_file_handler = RotatingFileHandler(
            file_location, maxBytes=1000 * 1000, backupCount=5
        )
        exp_file_handler.setLevel(logging.DEBUG)

        # create a formatter to format the log messages
        formatter = logging.Formatter(log_file_format)

        # set the formatter for the handlers
        exp_file_handler.setFormatter(formatter)

        # add the handlers to the logger
        self.logger.addHandler(exp_file_handler)

    def debug(self, message: str):
        """
        Log a debug message.

        :param message: the message to log
        """
        self.logger.debug(message)

    def info(self, message: str):
        """
        Log an info message.

        :param message: the message to log
        """
        self.logger.info(message)

    def warning(self, message: str):
        """
        Log a warning message.

        :param message: the message to log
        """
        self.logger.warning(message)

    def error(self, message: str):
        """
        Log an error message.

        :param message: the message to log
        """
        self.logger.error(message)
