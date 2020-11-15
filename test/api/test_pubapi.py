#!/usr/bin/env python3


import calendar
import os
from datetime import date, timedelta

import bitflyer
import pytest
import yaml


class TestPublicAPI():

    def test_get_market(self, pub_api, cases):
        cases = cases['get_market']
        # ck_res_arch(pub_api.get_market, cases)

        two_weeks_after = date.today() + timedelta(days=12)
        two_weeks_after_day = two_weeks_after.day
        two_weeks_after_month = calendar.month_abbr[two_weeks_after.month].upper()
        two_weeks_after_year = two_weeks_after.year

        markets = pub_api.get_market()

        for case in cases:
            if '{' in case['res']['product_code']:
                case['res']['product_code'] = case['res']['product_code'].format(two_weeks_after_day=two_weeks_after_day,
                                                                                 two_weeks_after_month=two_weeks_after_month,
                                                                                 two_weeks_after_year=two_weeks_after_year)
            assert case['res'] in markets

    def test_get_board(self, pub_api, cases):
        cases = cases['get_board']
        ck_res_arch(pub_api.get_board, cases)

    def test_get_ticker(self, pub_api, cases):
        cases = cases['get_ticker']
        ck_res_arch(pub_api.get_ticker, cases)

    def test_get_executions(self, pub_api, cases):
        cases = cases['get_executions']
        ck_res_arch(pub_api.get_executions, cases)

    def test_get_boardstate(self, pub_api, cases):
        cases = cases['get_boardstate']
        ck_res_arch(pub_api.get_boardstate, cases)


def ck_res_arch(api_func, cases):
    for case in cases:
        if 'req' in case.keys():
            res = api_func(*case['req'].values())
        else:
            res = api_func()

        case_res = case['res']

        # if the respose is list, do representative value test
        if isinstance(res, list):
            res = res[0]
            case_res = case_res[0]

        res_keys = res.keys()
        assert res_keys == case_res.keys()
        for res_key in res_keys:
            assert isinstance(res[res_key], type(case_res[res_key]))

            # if the value of dict is list
            if isinstance(res[res_key], list):
                for res_ch, case_ch in zip(res[res_key], case_res[res_key]):
                    assert isinstance(res_ch.values(), type(case_ch.values()))

            # if the value of dict is dict
            if isinstance(res[res_key], dict):
                assert res[res_key].values() == case_res[res_key].values()


@pytest.fixture
def pub_api():
    yield bitflyer.PublicAPI()
