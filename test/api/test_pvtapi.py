#!/usr/bin/env python3


import bitflyer
import pytest

from . import testmethod as testmt


class TestPrivateAPI():
    def test_get_permissions(self, pvt_api, cases):
        testmt.ck_perfect_match(pvt_api.get_permissions,
                                cases['get_permissions'])

    @pytest.mark.skip(reason='pytestskip')
    def test_get_permissions_forbidden(self, pvt_api, cases):
        testmt.ck_part_match(pvt_api.get_permissions,
                             cases['forbidden_permissions'])


@pytest.fixture
def pvt_api():
    yield bitflyer.PrivateAPI()
