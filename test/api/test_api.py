#!/usr/bin/env python3


import calendar
import json
import os
from datetime import date, timedelta

import bitflyer
import pytest

from . import testmethod as testmt

with open(f'{os.path.dirname(__file__)}/assets/testcases_api.json', 'r') as f:
    cases = json.load(f)


class TestPublicAPI():
    @pytest.mark.parametrize('case', cases['get_market'])
    def test_get_market(self, pub_api, case):
        # ck_res_arch(pub_api.get_market, cases)
        two_weeks_after = date.today() + timedelta(days=14-((date.today().weekday()+2) % 6+1))
        two_weeks_after_day = two_weeks_after.day
        two_weeks_after_month = calendar.month_abbr[two_weeks_after.month].upper()
        two_weeks_after_year = two_weeks_after.year

        if '{' in case['res']['product_code']:
            case['res']['product_code'] = case['res']['product_code'].format(two_weeks_after_day=two_weeks_after_day,
                                                                             two_weeks_after_month=two_weeks_after_month,
                                                                             two_weeks_after_year=two_weeks_after_year)
        testmt.ck_parts_match(pub_api.get_market, case)

    @pytest.mark.parametrize('case', cases['get_board'])
    def test_get_board(self, pub_api, case):
        testmt.ck_res_arch(pub_api.get_board, case)

    @pytest.mark.parametrize('case', cases['get_ticker'])
    def test_get_ticker(self, pub_api, case):
        testmt.ck_res_arch(pub_api.get_ticker, case)

    @pytest.mark.parametrize('case', cases['get_executions'])
    def test_get_executions(self, pub_api, case):
        testmt.ck_res_arch(pub_api.get_executions, case)

    @pytest.mark.parametrize('case', cases['get_boardstate'])
    def test_get_boardstate(self, pub_api, case):
        testmt.ck_res_arch(pub_api.get_boardstate, case)

    @pytest.mark.parametrize('case', cases['get_health'])
    def test_get_health(self, pub_api, case):
        testmt.ck_res_arch(pub_api.get_health, case)

    @pytest.mark.parametrize('case', cases['get_chats'])
    def test_get_chats(self, pub_api, case):
        testmt.ck_res_arch(pub_api.get_chats, case)


class TestPrivateAPI():

    def test_get_key(self, pvt_api):
        assert pvt_api._get_key() is not None

    def test_get_secret(self, pvt_api):
        assert pvt_api._get_secret(pvt_api._get_key()) is not None

    @pytest.mark.parametrize('case', cases['get_permissions'])
    def test_get_permissions(self, pvt_api, case):
        testmt.ck_perfect_match(pvt_api.get_permissions, case)

    @pytest.mark.xfail
    @pytest.mark.parametrize('case', cases['forbidden_permissions'])
    def test_get_permissions_forbidden(self, pvt_api, case):
        testmt.ck_part_match(pvt_api.get_permissions, case)

    @pytest.mark.parametrize('case', cases['get_balance'])
    def test_get_balance(self, pvt_api, case):
        testmt.ck_res_arch(pvt_api.get_balance, case)

    @pytest.mark.parametrize('case', cases['get_collateral'])
    def test_get_collateral(self, pvt_api, case):
        testmt.ck_res_arch(pvt_api.get_collateral, case)


@pytest.fixture
def pvt_api():
    yield bitflyer.PrivateAPI()


@ pytest.fixture
def pub_api():
    yield bitflyer.PublicAPI()
