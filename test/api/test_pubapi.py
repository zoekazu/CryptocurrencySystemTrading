#!/usr/bin/env python3


import calendar
import os
from datetime import date, timedelta

import bitflyer
import pytest
import yaml


class TestPublicAPI():
    def _init(self):
        self.api = bitflyer.PublicAPI()
        self.cases = self._read_cases()

    def _read_cases(self):
        with open(f'{os.path.dirname(__file__)}/assets/testcases_pubapi.yaml', 'r') as yml:
            cases = yaml.load(yml, Loader=yaml.FullLoader)
        return cases

    def test_get_market(self):
        self._init()
        # two_weeks_after = date.today() + timedelta(days=13)
        # two_weeks_after_day = two_weeks_after.day
        # two_weeks_after_month = calendar.month_abbr(two_weeks_after.month).upper()
        # two_weeks_after_day = two_weeks_after.year

        test_dicts = self.cases['get_market']

        markets = self.api.get_market()

        for test_dict in test_dicts:
            assert test_dict in markets
