#!/usr/bin/env python3


import calendar
from datetime import date, timedelta

import bitflyer
import pytest

from . import testmethod as testmt


class TestPublicAPI():

    def test_get_market(self, pub_api, cases):
        cases = cases['get_market']
        # ck_res_arch(pub_api.get_market, cases)

        two_weeks_after = date.today() + timedelta(days=12)
        two_weeks_after_day = two_weeks_after.day
        two_weeks_after_month = calendar.month_abbr[two_weeks_after.month].upper()
        two_weeks_after_year = two_weeks_after.year

        for case in cases:
            if '{' in case['res']['product_code']:
                case['res']['product_code'] = case['res']['product_code'].format(two_weeks_after_day=two_weeks_after_day,
                                                                                 two_weeks_after_month=two_weeks_after_month,
                                                                                 two_weeks_after_year=two_weeks_after_year)
        testmt.ck_parts_match(pub_api.get_market, cases)

    def test_get_board(self, pub_api, cases):
        testmt.ck_res_arch(pub_api.get_board, cases['get_board'])

    def test_get_ticker(self, pub_api, cases):
        testmt.ck_res_arch(pub_api.get_ticker, cases['get_ticker'])

    def test_get_executions(self, pub_api, cases):
        testmt.ck_res_arch(pub_api.get_executions, cases['get_executions'])

    def test_get_boardstate(self, pub_api, cases):
        testmt.ck_res_arch(pub_api.get_boardstate, cases['get_boardstate'])

    def test_get_health(self, pub_api, cases):
        testmt.ck_res_arch(pub_api.get_health, cases['get_health'])

    def test_get_chats(self, pub_api, cases):
        testmt.ck_res_arch(pub_api.get_chats, cases['get_chats'])


@ pytest.fixture
def pub_api():
    yield bitflyer.PublicAPI()
