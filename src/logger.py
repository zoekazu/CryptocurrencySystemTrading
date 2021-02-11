#!/usr/bin/env python3

import logging
from logging import Formatter, StreamHandler, getLogger, FileHandler

# set logger
# declear logger object
logger = getLogger("Logger")

# set logging level
logger.setLevel(logging.DEBUG)

# set handler
# declear handler
handler = StreamHandler()

# set handler level
handler.setLevel(logging.DEBUG)

# log format
handler_format = Formatter('%(asctime)s: [%(levelname)s]: %(filename)s-%(lineno)dline: %(message)s')
handler.setFormatter(handler_format)

# set file handler
file_handler = FileHandler('log.txt')
file_handler.set(logging.DEBUG)

logger.addHandler(handler)
logger.addHandler(file_handler)