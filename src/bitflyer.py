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


class PublicRequest(Enum):
    getmarket = "/v1/getmarkets"
    getborad = "/v1/getboard"
    getticker = "/v1/getticker"
    getexecutions = "/v1/getexecutions"
    getboardstate = "/v1/getboardstate"
    gethealth = "/v1/gethealth"
    getchats = "/v1/getchats"


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


class ProductCode(Enum):
    btc_jpy = "BTC_JPY"
    fx_btc_jpy = "FX_BTC_JPY"
    eth_btc = "ETH_BTC"
    bhc_btc = "BCH_BTC"
    eth_jpy = "ETH_JPY"


class State(Enum):
    runnning = "RUNNING"
    clozed = "CLOZED"
    starting = "STARTING"
    preopen = "PREOPEN"
    circuit_break = "CIRCUIT BREAK"
    awaiting_sq = "AWAITING SQ"
    matured = "MATURED"


class Health(Enum):
    normal = "NORMAL"
    busy = "BUSY"
    very_busy = "VERY BUSY"
    super_busy = "SUPER BUSY"
    no_order = "NO_ORDER"
    stop = "STOP"


class Side(Enum):
    buy = "BUY"
    sell = "SELL"

# TODO: timestamp dataclass implementation


def str2dataclass(val, data_class: dataclass):
    if isinstance(val, str):
        return data_class(val)
    return val


@dataclass(frozen=True)
class ResGetMarket:
    product_code: Union[str, ProductCode]
    market_type: str
    alias: str = None

    def __pos_init__(self):
        self.product_code = str2dataclass(self.product_code, ProductCode)

    def dict_factory(self, val):
        return dict(x for x in val if (x[0] != "alias") or (x[1] is not None))


@dataclass(frozen=True)
class PriceSize:
    price: int
    size: float


@dataclass(frozen=True)
class ResGetBoard:
    mid_price: float
    bids: List[Union[str, PriceSize]]
    asks: List[Union[str, PriceSize]]

    def __pos_init__(self):
        self.bids = [str2dataclass(bid, PriceSize) for bid in self.bids]
        self.bids = [str2dataclass(ask, PriceSize) for ask in self.asks]


@dataclass
class Period:
    before: int = None
    after: int = None
    count: int = COUNT_DEF


@dataclass(frozen=True)
class ResGetTicker:
    product_code: Union[str, ProductCode]
    state: State
    timestamp: str
    tick_id: int
    best_bid: float
    best_ask: float
    best_bid_size: float
    best_ask_size: float
    total_bid_depth: float
    total_ask_depth: float
    market_bid_size: float
    market_ask_size: float
    ltp: float
    volume: float
    volume_by_product: float

    def __pos_init__(self):
        self.product_code = str2dataclass(self.product_code, ProductCode)


@dataclass(frozen=True)
class ResGetExecutions:
    id: int
    side: Side
    price: float
    size: float
    exec_date: str
    buy_child_order_acceptance_id: str
    sell_child_order_acceptance_id: str


@dataclass(frozen=True)
class ResGetBoardState:
    health: Union[str, Health]
    state: State

    def __pos_init__(self):
        self.health = str2dataclass(self.health, Health)


@dataclass(frozen=True)
class ResGetHealth:
    status: Union[str, State]

    def __pos_init__(self):
        self.status = str2dataclass(self.status, State)


@dataclass(frozen=True)
class ResGetChats:
    nickname: str
    message: str
    date: str


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
            params = {"poduct_code": self.product_code,
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

    def _request(self, req_http, req_params=None):
        url = self.api_url + req_http

        try:
            with requests.Session() as s:
                res = s.get(url, params=req_params, timeout=self.timeout)
        except requests.RequestException as err:
            raise err

        if res.status_code == requests.codes.ok:
            # if the response is empty, return None
            return json.loads(res.content.decode("utf-8"))
        else:
            raise urllib.error.HTTPError

    def _get_listed_dataclass(self, res, data_class: dataclass) -> List[dataclass]:
        return [data_class(**x) for x in res]

    def get_market(self) -> List[ResGetMarket]:
        return self._get_listed_dataclass(self._request(PublicRequest.getmarket.value), ResGetMarket)

    def get_board(self, product_code: Union[str, ProductCode]) -> ResGetBoard:
        params = {"product_code": product_code.value}
        return ResGetBoard(**self._request(PublicRequest.getborad.value, req_params=params))

    def get_ticker(self, product_code: ProductCode) -> ResGetTicker:
        params = {"product_code": product_code.value}
        return ResGetTicker(**self._request(PublicRequest.getticker.value, req_params=params))

    def get_executions(self, product_code: ProductCode, period: Period = None) -> List[ResGetExecutions]:
        params = {"product_code": product_code.value,
                  "count": period.count}
        if period.before:
            params["before"] = period.before
        if period.after:
            params["after"] = period.after

        return self._get_listed_dataclass(self._request(PublicRequest.getexecutions.value, req_params=params), ResGetExecutions)

    def get_boardstate(self, product_code: ProductCode):
        params = {"product_code": product_code.value}
        return ResGetBoardState(**self._request(PublicRequest.getboardstate.value, req_params=params))

    def get_health(self, product_code: ProductCode) -> ResGetHealth:
        params = {"product_code": product_code.value}
        return ResGetHealth(**self._request(PublicRequest.gethealth.value, req_params=params))

    def get_chats(self, from_date: int = 5) -> List[ResGetChats]:
        params = {"from_date": from_date}
        return self._get_listed_dataclass(self._request(PublicRequest.getchats.value, req_params=params), ResGetChats)


class PrivateAPI(API):
    def __init__(self, timeout=TIMEOUT_DEF):
        super().__init__()
        self.api_name = API_NAME
        self.api_key = self._get_key()
        self.api_secret = self._get_secret(self.api_key)
        self.timeout = timeout

    def _get_key(self):
        key = keyring.get_password(self.api_name, self.api_name + "_id")
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
        return self._request(*PRIREQ_PATH_METHOD["getcollateral"])

    def get_collateralaccounts(self):
        return self._request(*PRIREQ_PATH_METHOD["getcollateralaccounts"])

    def get_addresses(self):
        return self._request(*PRIREQ_PATH_METHOD["getaddresses"])

    def get_coinins(self, before=None, after=None, count=COUNT_DEF):
        params = {"count": count}
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        return self._request(*PRIREQ_PATH_METHOD["getcoinins"], params=params)

    def get_coinouts(self, before=None, after=None, count=COUNT_DEF):
        params = {"count": count}
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        return self._request(*PRIREQ_PATH_METHOD["getcoinouts"], params=params)

    def get_bankaccounts(self):
        return self._request(*PRIREQ_PATH_METHOD["getbankaccounts"])

    def get_deposits(self, before=None, after=None, count=COUNT_DEF):
        params = {"count": count}
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        return self._request(*PRIREQ_PATH_METHOD["getdeposits"], params=params)

    def withdraw(self, currency_mode, bank_account_id, amount, code=None):
        params = {"currency_mode": currency_mode,
                  "bank_account_id": bank_account_id,
                  "amount": amount}
        if code:
            params["code"] = code
        return self._request(*PRIREQ_PATH_METHOD["withdraw"])

    def get_withdrawals(self, before=None, after=None, count=COUNT_DEF, message_id=None):
        params = {"count": count}
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        if message_id:
            params["message_id"] = message_id
        return self._request(*PRIREQ_PATH_METHOD["getwithdrawals"], params=params)

    def send_childorder(self, product_code, child_order_type, side, size, price=None, minute_to_expire=43200, time_in_force="GTC"):
        if product_code == "BTC_JPY":
            if size < 0.001:
                raise ValueError('Minimum bet is 0.001')
        else:  # product_code == "ETH_JPY"
            if size < 0.01:
                raise ValueError('Minimum bet is 0.01')

        params = {"product_code": product_code,
                  "child_order_type": child_order_type,
                  "side": side,
                  "size": size,
                  "minute_to_expire": minute_to_expire,
                  "time_in_force": time_in_force}

        if child_order_type == "LIMIT":
            if not price:
                raise ValueError
            params["price"] = price

        return self._request(*PRIREQ_PATH_METHOD["sendchildorder"], params=params)

    def cancel_childorder(self, product_code, child_order_id=None, child_order_acceptance_id=None):
        params = {"product_code": product_code}
        if child_order_id and child_order_acceptance_id:
            raise ValueError
        elif child_order_id:
            params["child_order_id"] = child_order_id
        elif child_order_acceptance_id:
            params["child_order_acceptance_id"] = child_order_acceptance_id
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
        params = {"product_code": product_code}
        if parent_order_id and parent_order_acceptance_id:
            raise ValueError
        elif parent_order_id:
            params["parent_order_id"] = parent_order_id
        elif parent_order_acceptance_id:
            params["parent_order_acceptance_id"] = parent_order_acceptance_id
        else:
            raise ValueError

        return self._request(*PRIREQ_PATH_METHOD["cancelparentorder"], params=params)

    def cancel_allchildorders(self, product_code):
        params = {"product_code": product_code}
        return self._request(*PRIREQ_PATH_METHOD["cancelallchildorders"], params=params)

    def get_childorders(self, product_code, before=None, after=None, count=COUNT_DEF, child_order_state=None,
                        child_order_id=None, child_order_acceptance_id=None, parent_order_id=None):
        params = {"product_code": product_code,
                  "count": count}
        if before:
            params["before"] = before
        if after:
            params["after"] = after

        param_num = sum(bool(i) for i in [child_order_state, child_order_id,
                                          child_order_acceptance_id, parent_order_id])
        if param_num == 0:
            pass
        elif param_num > 1:
            raise ValueError
        elif child_order_state:
            params["child_order_state"] = child_order_state
        elif child_order_id:
            params["child_order_id"] = child_order_id
        elif child_order_acceptance_id:
            params["child_order_acceptance_id"] = child_order_acceptance_id
        else:  # parent_order_id == True
            params["parent_order_id"] = parent_order_id

        return self._request(*PRIREQ_PATH_METHOD["getchildorders"], params=params)

    def get_parentorders(self, product_code, before=None, after=None, count=COUNT_DEF,
                         parent_order_state=None):
        params = {"product_code": product_code,
                  "count": count}
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        if parent_order_state:
            params["parent_order_state"] = parent_order_state

        return self._request(*PRIREQ_PATH_METHOD["getparentorders"], params=params)

    def get_parentorder(self, parent_order_id=None, parent_order_acceptance_id=None):
        if parent_order_id and parent_order_acceptance_id:
            raise ValueError
        elif parent_order_id:
            params = {"parent_order_id": parent_order_id}
        elif parent_order_acceptance_id:
            params = {"parent_order_acceptance_id": parent_order_acceptance_id}
        else:
            raise ValueError
        return self._request(*PRIREQ_PATH_METHOD["getparentorder"], params=params)

    def get_executions(self, product_code, before=None, after=None, count=COUNT_DEF,
                       child_order_id=None, child_order_acceptance_id=None):
        params = {"product_code": product_code,
                  "count": count}
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        if child_order_id:
            params["child_order_id"] = child_order_id
        if child_order_acceptance_id:
            params["child_order_acceptance_id"] = child_order_acceptance_id
        return self._request(*PRIREQ_PATH_METHOD["getexecutions"], params=params)

    def get_balancehistory(self, currency_code, before=None, after=None, count=COUNT_DEF):
        params = {"currency_code": currency_code,
                  "count": count}
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        return self._request(*PRIREQ_PATH_METHOD["getbalancehistory"], params=params)

    def get_positions(self, product_code):
        params = {"product_code": product_code}
        return self._request(*PRIREQ_PATH_METHOD["getpositions"], params=params)

    def get_collateralhistory(self, before=None, after=None, count=COUNT_DEF):
        params = {"count": count}
        if before:
            params["before"] = before
        if after:
            params["after"] = after
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
