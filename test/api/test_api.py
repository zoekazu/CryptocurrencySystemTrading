#!/usr/bin/env python3


import calendar
import json
import os
from datetime import date, timedelta

import bitflyer
import pytest
import requests

from . import testmethod as testmt

with open(f'{os.path.dirname(__file__)}/assets/testcases_api.json', 'r', encoding="utf-8") as f:
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
            return None
            case['res']['product_code'] = case['res']['product_code'].format(two_weeks_after_day=two_weeks_after_day,
                                                                             two_weeks_after_month=two_weeks_after_month,
                                                                             two_weeks_after_year=two_weeks_after_year)
        testmt.ck_part_match(pub_api.get_market, case)

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

    @pytest.mark.skip(reason="Unimplemented function")
    @pytest.mark.parametrize('case', cases['get_collateralaccounts'])
    def test_get_collateralaccounts(self, pvt_api, case):
        testmt.ck_res_arch(pvt_api.get_collateralaccounts, case)

    @pytest.mark.parametrize('case', cases['get_addresses'])
    def test_get_addresses(self, pvt_api, case):
        testmt.ck_res_arch(pvt_api.get_addresses, case)

    @pytest.mark.skip(reason="Unimplemented function")
    @pytest.mark.parametrize('case', cases['get_coinins'])
    def test_get_coinins(self, pvt_api, case):
        testmt.ck_res_arch(pvt_api.get_coinins, case)

    @pytest.mark.parametrize('case', cases['get_coinouts'])
    def test_get_coinouts(self, pvt_api, case):
        testmt.ck_res_arch(pvt_api.get_coinouts, case)

    @pytest.mark.parametrize('case', cases['get_bankaccounts'])
    def test_get_bankaccounts(self, pvt_api, case):
        testmt.ck_res_arch(pvt_api.get_bankaccounts, case)

    @pytest.mark.parametrize('case', cases['get_deposits'])
    def test_get_deposits(self, pvt_api, case):
        testmt.ck_res_arch(pvt_api.get_deposits, case)

    @pytest.mark.xfail(reason="Unauthorized API")
    @pytest.mark.parametrize('case', cases['withdraw'])
    def test_withdraw(self, pvt_api, case):
        testmt.ck_res_arch(pvt_api.withraw, case)

    @pytest.mark.xfail(reason="Unauthorized API")
    @pytest.mark.parametrize('case', cases['withdraw_err'])
    def test_withdraw_err(self, pvt_api, case):
        testmt.ck_res_arch(pvt_api.withdraw, case)

    @pytest.mark.xfail(reason="Unauthorized API")
    @pytest.mark.parametrize('case', cases['get_withdrawals'])
    def test_get_withdrawals(self, pvt_api, case):
        testmt.ck_res_arch(pvt_api.get_withdrawals, case)

    @pytest.mark.skip(reason="Do not run transactions")
    @pytest.mark.parametrize('case', cases['send_childorder'])
    def test_send_childorder(self, pvt_api, case):
        testmt.ck_res_arch(pvt_api.send_childorder, case)

    @pytest.mark.parametrize('case', cases['cancel_childorder'])
    def test_cancel_childorder(self, pvt_api, case):
        # This test case also tests send_childorder()
        order_id = pvt_api.send_childorder(**case['req'])
        res_status = pvt_api.cancel_childorder(product_code=case['req']['product_code'],
                                               child_order_acceptance_id=order_id['child_order_acceptance_id'])
        testmt.ck_res_status(res_status)

    def dict2orderparams_incase(self, case):
        return [bitflyer.OrderParams(**param) for param in case["req"]["parameters"]]

    @pytest.mark.skip(reason="Do not run transactions")
    @pytest.mark.parametrize('case', cases['send_ifd'])
    def test_send_ifd(self, pvt_api, case):
        order_params = self.dict2orderparams_incase(case)
        del case['req']['parameters']
        _ = pvt_api.send_ifd(*order_params, **case['req'])

    @pytest.mark.skip(reason="Do not run transactions")
    @pytest.mark.parametrize('case', cases['send_oco'])
    def test_send_oco(self, pvt_api, case):
        order_params = self.dict2orderparams_incase(case)
        del case['req']['parameters']
        _ = pvt_api.send_oco(*order_params, **case['req'])

    @pytest.mark.skip(reason="Do not run transactions")
    @pytest.mark.parametrize('case', cases['send_ifdoco'])
    def test_send_ifdoco(self, pvt_api, case):
        order_params = self.dict2orderparams_incase(case)
        del case['req']['parameters']
        _ = pvt_api.send_ifdoco(*order_params, **case['req'])

    @pytest.mark.parametrize('case', cases['send_ifdoco'])
    def test_cancel_parentorder(self, pvt_api, case):
        order_params = self.dict2orderparams_incase(case)
        product_code = case['req']['parameters'][0]['product_code']
        del case['req']['parameters']
        order_id = pvt_api.send_ifdoco(*order_params, **case['req'])
        res_status = pvt_api.cancel_parentorder(product_code=product_code,
                                                parent_order_acceptance_id=order_id['parent_order_acceptance_id'])
        testmt.ck_res_status(res_status)

    @pytest.mark.parametrize('cases', cases['cancel_allchildorders'])
    def test_cancel_allchildorders(self, pvt_api, cases):
        for case in cases:
            pvt_api.send_childorder(**case['req'])
        res_status = pvt_api.cancel_allchildorders(product_code=case['req']['product_code'])
        testmt.ck_res_status(res_status)
    
    @pytest.mark.parametrize('case', cases['get_childorders'])
    def test_get_childorders(self, pvt_api, case):
        testmt.ck_res_arch(pvt_api.get_childorders, case)


@ pytest.fixture
def pvt_api():
    yield bitflyer.PrivateAPIWapper()


@ pytest.fixture
def pub_api():
    yield bitflyer.PublicAPI()
