#!/usr/bin/env python3

import abc
import hashlib
import hmac
import json
import time
import urllib
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Union

import keyring
import requests

API_NAME = "Bitflyer"
API_URL = "https://api.bitflyer.com"
TIMEOUT_DEF = 5
COUNT_DEF = 100


class APIConfigError(Exception):
    pass


class APIParamsError(Exception):
    pass


class HTTPStatusError(Exception):
    pass


class API(metaclass=abc.ABCMeta):
    def __init__(self, timeout=TIMEOUT_DEF):
        self.api_url = API_URL
        self.api_name = API_NAME
        self.timeout = timeout
        # TODO: implemetation of logger

    @abc.abstractclassmethod
    def _request(self):
        pass
