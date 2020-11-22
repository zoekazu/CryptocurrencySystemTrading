#!/usr/bin/env python3

import abc
import hashlib
import hmac
import json
import time
import urllib
from dataclasses import dataclass

import keyring
import requests

API_NAME = "Bitflyer"
API_URL = "https://api.bitflyer.com"
TIMEOUT_DEF = 5
COUNT_DEF = 100

PUBREQ_PATH = {
    "getmarket": "/v1/getmarkets",
    "board": "/v1/getboard",
    "getticker": "/v1/getticker",
    "getexecutions": "/v1/getexecutions",
    "getboardstate": "/v1/getboardstate",
    "gethealth": "/v1/gethealth",
    "getchats": "/v1/getchats"
}

PRIREQ_PATH_METHOD = {
    "getpermissions": ["/v1/me/getpermissions", "GET"],
    "getbalance": ["/v1/me/getbalance", "GET"],
    "getcollateral": ["/v1/me/getcollateral", "GET"],
    "getcollateralaccounts": ["/v1/me/getcollateralaccounts", "GET"],
    "getaddresses": ["/v1/me/getaddresses", "GET"],
    "getcoinins": ["/v1/me/getcoinins", "GET"],
    "getcoinouts": ["/v1/me/getcoinouts", "GET"],
    "getbankaccounts": ["/v1/me/getbankaccounts", "GET"],
    "getdeposits": ["/v1/me/getdeposits", "GET"],
    "withdraw": ["/v1/me/withdraw", "POST"],
    "getwithdrawals": ["/v1/me/getwithdrawals", "GET"],
    "sendchildorder": ["/v1/me/sendchildorder", "POST"],
    "cancelchildorder": ["/v1/me/cancelchildorder", "POST"],
    "sendparentorder": ["/v1/me/sendparentorder", "POST"],
    "cancelparentorder": ["/v1/me/cancelparentorder", "POST"],
    "cancelallchildorders": ["/v1/me/cancelallchildorders", "POST"],
    "getchildorders": ["/v1/me/getchildorders", "GET"],
    "getparentorders": ["/v1/me/getparentorders", "GET"],
    "getparentorder": ["/v1/me/getparentorder", "GET"],
    "getexecutions": ["/v1/me/getexecutions", "GET"],
    "getbalancehistory": ["/v1/me/getbalancehistory", "GET"],
    "getpositions": ["/v1/me/getpositions", "GET"],
    "getcollateralhistory": ["/v1/me/getcollateralhistory", "GET"],
    "gettradingcommission": ["/v1/me/gettradingcommission", "GET"]
}


class APIConfigError(Exception):
    pass


class APIParamsError(Exception):
    pass


class HTTPStatusError(Exception):
    pass


@dataclass
class OrderParams:
    product_code: str
    condition_type: str
    side: str
    size: float
    price: float = None

    def __post_init__(self):
        if (self.condition_type == "LIMIT") or (self.condition_type == "STOP_LIMIT"):
            if not self.price:
                raise ValueError

    def dump_dict(self):
        if (self.condition_type == "LIMIT") or (self.condition_type == "STOP_LIMIT"):
            params = {"product_code": self.product_code,
                      "condition_type": self.condition_type,
                      "side": self.side,
                      "price": self.price,
                      "size": self.size}
        else:
            params = {"product_code": self.product_code,
                      "condition_type": self.condition_type,
                      "side": self.side,
                      "size": self.size}
        return params


class API(metaclass=abc.ABCMeta):
    def __init__(self):
        self.api_url = API_URL

    @abc.abstractclassmethod
    def _request(self):
        pass


class PublicAPI(API):
    def __init__(self, timeout=TIMEOUT_DEF):
        super().__init__()
        self.timeout = timeout

    def _request(self, path, params=None, timeout=None):
        if timeout is None:
            timeout = self.timeout

        url = self.api_url + path

        try:
            with requests.Session() as s:
                res = s.get(url, params=params, timeout=timeout)
        except requests.RequestException as err:
            raise err

        if res.status_code == requests.codes.ok:
            return json.loads(res.content.decode("utf-8"))
        else:
            raise HTTPStatusError('You accessed ' + url
                                  + ' but got a ' + str(res.status_code)
                                  + ' HTTP status code error')

    def get_market(self):
        return self._request(PUBREQ_PATH["getmarket"])

    def get_board(self, product_code):
        params = {"product_code": product_code}
        return self._request(PUBREQ_PATH["board"], params=params)

    def get_ticker(self, product_code):
        params = {"product_code": product_code}
        return self._request(PUBREQ_PATH["getticker"], params=params)

    def get_executions(self, product_code, before, after, count=COUNT_DEF):
        params = {"product_code": product_code,
                  "count": count,
                  "before": before,
                  "after": after}
        return self._request(PUBREQ_PATH["getexecutions"], params=params)

    def get_boardstate(self, product_code):
        params = {"product_code": product_code}
        return self._request(PUBREQ_PATH["getboardstate"], params=params)

    def get_health(self, product_code):
        params = {"product_code": product_code}
        return self._request(PUBREQ_PATH["gethealth"], params=params)

    def get_chats(self, from_date=5):
        params = {"from_date": from_date}
        return self._request(PUBREQ_PATH["getchats"], params=params)


class PrivateAPI(API):
    def __init__(self, timeout=TIMEOUT_DEF):
        super().__init__()
        self.api_name = API_NAME
        self.api_key = self._get_key()
        self.api_secret = self._get_secret(self.api_key)
        self.timeout = timeout

    def _get_key(self):
        key = keyring.get_password(self.api_name, self.api_name+"_id")
        if key is None:
            raise APIConfigError('Invalid api_name of API')
        return key

    def _get_secret(self, key):
        secret = keyring.get_password(self.api_name, key)
        if secret is None:
            raise APIConfigError('Invalid user_name of API')
        return secret

    def _request(self, path, method, params=None, timeout=None):
        if timeout is None:
            timeout = self.timeout

        url = self.api_url + path
        body = ""
        headers = None

        if method == "POST":
            body = json.dumps(params)
        elif method == "GET":
            if params:
                body = "?" + urllib.parse.urlencode(params)
        else:
            raise APIConfigError("Invalid HTTP method")

        api_secret = str.encode(self.api_secret)
        timestamp = str(time.time())
        text = str.encode(timestamp + method + path + body)
        sign = hmac.new(api_secret, text, hashlib.sha256).hexdigest()

        headers = {
            "ACCESS-KEY": self.api_key,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-SIGN": sign,
            "Content-Type": "application/json"
        }

        try:
            with requests.Session() as s:
                if headers:
                    s.headers.update(headers)
                if method == "GET":
                    res = s.get(url, params=params, timeout=timeout)
                else:  # method == "POST"
                    res = s.post(url, data=json.dumps(params), timeout=timeout)
        except requests.RequestException as err:
            raise err

        if res.status_code == requests.codes.ok:
            if res.content:
                return json.loads(res.content.decode("utf-8"))
            else:
                return res.status_code
        else:
            raise HTTPStatusError('HTTP status ' +
                                  str(res.status_code) +
                                  ', :' +
                                  str(res.text) +
                                  ', URL: ' +
                                  str(res.url))

    def get_permissions(self):
        return self._request(*PRIREQ_PATH_METHOD["getpermissions"])

    def get_balance(self):
        return self._request(*PRIREQ_PATH_METHOD["getbalance"])

    def get_collateral(self):
        """get the status of deposit

        Returns:
            dict:   {
                    "collateral": 100000,
                    "open_position_pnl": -715,
                    "require_collateral": 19857,
                    "keep_rate": 5.000
                    }
        """
        return self._request(*PRIREQ_PATH_METHOD["getcollateral"])

    def get_collateralaccounts(self):
        """get the status of deposit for each currency

        Returns:
            dict:   {
                        {
                            "currency_code": "JPY",
                            "amount": 10000
                        },
                        {
                            "currency_code": "BTC",
                            "amount": 1.23
                        }
                    }
        """
        return self._request(*PRIREQ_PATH_METHOD["getcollateralaccounts"])

    def get_addresses(self):
        return self._request(*PRIREQ_PATH_METHOD["getaddresses"])

    def get_coinins(self, before, after, count=COUNT_DEF):
        params = {"count": count,
                  "before": before,
                  "after": after}
        return self._request(*PRIREQ_PATH_METHOD["getcoinins"], params=params)

    def get_coinouts(self, before, after, count=COUNT_DEF):
        params = {"count": count,
                  "before": before,
                  "after": after}
        return self._request(*PRIREQ_PATH_METHOD["getcoinouts"], params=params)

    def get_bankaccounts(self):
        return self._request(*PRIREQ_PATH_METHOD["getbankaccounts"])

    def get_deposits(self, before, after, count=COUNT_DEF):
        return self._request(*PRIREQ_PATH_METHOD["getdeposits"])

    def withdraw(self, currency_mode, bank_account_id, amount, code=None):
        params = {"currency_mode": currency_mode,
                  "bank_account_id": bank_account_id,
                  "amount": amount}
        if code:
            params["code"] = code
        return self._request(*PRIREQ_PATH_METHOD["withdraw"])

    def get_withdrawals(self, before, after, count=COUNT_DEF, message_id=None):
        params = {"count": count,
                  "before": before,
                  "after": after,
                  "message_id": message_id}
        return self._request(*PRIREQ_PATH_METHOD["getwithdrawals"], params=params)

    def send_childorder(self, product_code, child_order_type, side, size, price=None, minute_to_expire=43200, time_in_force="GTC"):
        """
        BTC_JPY: 0.001
        RTH_JPY: 0.01
        """
        if child_order_type == "LIMIT":
            if not price:
                raise ValueError
            params = {"product_code": product_code,
                      "child_order_type": child_order_type,
                      "side": side,
                      "price": price,
                      "size": size,
                      "minute_to_expire": minute_to_expire,
                      "time_in_force": time_in_force}

        else:  # child_order_type == "MARKET"
            params = {"product_code": product_code,
                      "child_order_type": child_order_type,
                      "side": side,
                      "size": size,
                      "minute_to_expire": minute_to_expire,
                      "time_in_force": time_in_force}
        return self._request(*PRIREQ_PATH_METHOD["sendchildorder"], params=params)

    def cancel_childorder(self, product_code, child_order_id=None, child_order_acceptance_id=None):
        if child_order_id and child_order_acceptance_id:
            raise ValueError
        elif child_order_id:
            params = {"product_code": product_code,
                      "child_order_id": child_order_id}
        elif child_order_acceptance_id:
            params = {"product_code": product_code,
                      "child_order_acceptance_id": child_order_acceptance_id}
        else:
            raise ValueError

        return self._request(*PRIREQ_PATH_METHOD["cancelchildorder"], params=params)

    def _send_parentorder(self, order_method, send_param, minute_to_expire=43200, time_in_force="GTC"):
        # NOTE: This function is called from warraper because send_params are complicated

        params = {"order_method": order_method,
                  "minute_to_expire": minute_to_expire,
                  "time_in_force": time_in_force,
                  "parameters": send_param}
        return self._request(*PRIREQ_PATH_METHOD["sendparentorder"], params=params)

    def cancel_parentorder(self, product_code, parent_order_id=None, parent_order_acceptance_id=None):
        if parent_order_id and parent_order_acceptance_id:
            raise ValueError
        elif parent_order_id:
            params = {"product_code": product_code,
                      "parent_order_id": parent_order_id}
        elif parent_order_acceptance_id:
            params = {"product_code": product_code,
                      "parent_order_acceptance_id": parent_order_acceptance_id}
        else:
            raise ValueError

        return self._request(*PRIREQ_PATH_METHOD["cancelparentorder"], params=params)

    def cancel_allchildorders(self, product_code):
        params = {"product_code": product_code}
        return self._request(*PRIREQ_PATH_METHOD["cancelallchildorders"], params=params)

    def get_childorders(self, product_code, count, before, after, child_order_state=None,
                        child_order_id=None, child_order_acceptance_id=None, parent_order_id=None):
        params = {"product_code": product_code,
                  "count": count,
                  "before": before,
                  "after": after}
        if child_order_state:
            params["child_order_state"] = child_order_state
        if child_order_id:
            params["child_order_id"] = child_order_id
        if child_order_acceptance_id:
            params["child_order_acceptance_id"] = child_order_acceptance_id
        if parent_order_id:
            params["parent_order_id"] = parent_order_id
        return self._request(*PRIREQ_PATH_METHOD["getchildorders"], params=params)

    def get_parentorders(self, product_code, before, after, count=COUNT_DEF,
                         parent_order_state=None):
        params = {"product_code": product_code,
                  "count": count,
                  "before": before,
                  "after": after,
                  "parent_order_state": parent_order_state}
        return self._request(*PRIREQ_PATH_METHOD["getparentorders"], params=params)

    def get_parentorder(self, parent_order_id=None, parent_order_acceptance_id=None):
        if not bool(parent_order_id) ^ bool(parent_order_acceptance_id):
            raise APIParamsError("Invaild parameters")
        if parent_order_id:
            params = {"parent_order_id": parent_order_id}
        else:
            params = {"parent_order_acceptance_id": parent_order_acceptance_id}
        return self._request(*PRIREQ_PATH_METHOD["getparentorder"], params=params)

    def get_executions(self, product_code, before, after, count=COUNT_DEF,
                       child_order_id=None, child_order_acceptance_id=None):
        params = {"product_code": product_code,
                  "count": count,
                  "before": before,
                  "after": after}
        if child_order_id:
            params["child_order_id"] = child_order_id
        if child_order_acceptance_id:
            params["child_order_acceptance_id"] = child_order_acceptance_id
        return self._request(*PRIREQ_PATH_METHOD["getexecutions"], params=params)

    def get_balancehistory(self, currency_code, before, after, count=COUNT_DEF):
        params = {"currency_code": currency_code,
                  "count": count,
                  "before": before,
                  "after": after}
        return self._request(*PRIREQ_PATH_METHOD["getbalancehistory"], params=params)

    def get_positions(self, product_code):
        params = {"product_code": product_code}
        return self._request(*PRIREQ_PATH_METHOD["getpositions"], params=params)

    def get_collateralhistory(self, before, after, count=COUNT_DEF):
        params = {"count": count,
                  "before": before,
                  "after": after}
        return self._request(*PRIREQ_PATH_METHOD["getcollateralhistory"], params=params)

    def get_tradingcommission(self, product_code):
        params = {"product_code": product_code}
        return self._request(*PRIREQ_PATH_METHOD["gettradingcommission"], params=params)


class PrivateAPIWapper(PrivateAPI):
    def __init__(self):
        super().__init__()

    def send_ifd(self, params_1: OrderParams, params_2: OrderParams, minute_to_expire=43200, time_in_force="GTC"):
        params = [params_1.dump_dict(), params_2.dump_dict()]
        return self._send_parentorder("IFD", params, minute_to_expire=43200, time_in_force="GTC")

    def send_oco(self, params_1: OrderParams, params_2: OrderParams, minute_to_expire=43200, time_in_force="GTC"):
        params = [params_1.dump_dict(), params_2.dump_dict()]
        return self._send_parentorder("OCO", params, minute_to_expire=43200, time_in_force="GTC")

    def send_ifdoco(self, params_1: OrderParams, params_2: OrderParams, params_3: OrderParams, minute_to_expire=43200, time_in_force="GTC"):
        params = [params_1.dump_dict(), params_2.dump_dict(), params_3.dump_dict()]
        return self._send_parentorder("IFDOCO", params, minute_to_expire=43200, time_in_force="GTC")


class PublicAPITest:
    def __init__(self):
        self.product_codes = ['BTC_JPY', 'ETH_JPY', 'FX_BTC_JPY', 'ETH_BTC', 'BCH_BTC']
        self.API = PublicAPI()

    def get_market_test(self):
        a = self.API.get_market()
        b = a[0]
        print(type(a))
        print(type(b))
        print(a)

    def get_board_test(self):
        for product_code in self.product_codes:
            print(self.API.get_board(product_code))


class PrivateAPITest:
    def __init__(self):
        self.API = PrivateAPI()

    def getpermissions(self):
        print(self.API.get_permissions())


def run_test():
    public_module = PublicAPITest()
    public_module.get_market_test()

    private_module = PrivateAPITest()
    private_module.getpermissions()

    # public_module.get_board_test()


if __name__ == '__main__':
    run_test()
