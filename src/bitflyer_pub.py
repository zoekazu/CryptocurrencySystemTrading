#!/usr/bin/env python3


import json
import urllib
from dataclasses import dataclass
from enum import Enum
from typing import List, Union

import requests

import bitflyer

COUNT_DEF = 100


class PublicRequest(Enum):
    getmarket = "/v1/getmarkets"
    getborad = "/v1/getboard"
    getticker = "/v1/getticker"
    getexecutions = "/v1/getexecutions"
    getboardstate = "/v1/getboardstate"
    gethealth = "/v1/gethealth"
    getchats = "/v1/getchats"


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


class PublicAPI(bitflyer.API):
    def __init__(self):
        super().__init__()

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


def run_test():
    public_module = PublicAPITest()
    public_module.get_market_test()
    # public_module.get_board_test()


if __name__ == '__main__':
    run_test()
