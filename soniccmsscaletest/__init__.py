#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .logger import setup_logger
logger = setup_logger()
import logging
subprocess_logger = setup_logger(
    'subprocess',
    logging.Formatter(fmt='[subprocess]: %(message)s')
    )

SCRAM_ARCH='slc7_amd64_gcc700'
DATE_FMT_STR='%Y-%m-%d %H:%M:%S'

from . import utils
from .inferencer import Inferencer
from .tarballmanager import TarballManager
from .jobfiles import JDLFile, SHFile
from .outputinterpreter import OutputInterpreter
