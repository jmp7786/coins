#! /usr/bin/env python
# XCoin API-call sample script (for Python 3.X)
#
# @author	btckorea
# @date	2017-04-11
#
#
# First, Build and install pycurl with the following commands::
# (if necessary, become root)
#
# https://pypi.python.org/pypi/pycurl/7.43.0#downloads
#
# tar xvfz pycurl-7.43.0.tar.gz
# cd pycurl-7.43.0
# python setup.py --libcurl-dll=libcurl.so install
# python setup.py --with-openssl install
# python setup.py install

import sys
from xcoin_api_client import *
import pprint


api_key = "197312a282546f44adf9d5671117483d";
api_secret = "0f00f3392ae9dc2adf16f2df59e8f01213e";

api = XCoinAPI(api_key, api_secret);

rgParams = {
	# "currency" : "ALL",
	# "payment_currency" : "KRW"
};


#
# public api
#
# /public/ticker
# /public/recent_ticker
# /public/orderbook
# /public/recent_transactions

result = api.xcoinApiCall("/public/orderbook/ALL", rgParams);
print("status: " + result["status"]);
pprint.pprint(result['data'])


# private api
#
# endpoint => parameters
# /info/current
# /info/account
# /info/balance
# /info/wallet_address
#
# result = api.xcoinApiCall("/info/account", {});
# print("status: " + result["status"]);
# print("created: " + result["data"]["created"]);
# print("account id: " + result["data"]["account_id"]);
# print("trade fee: " + result["data"]["trade_fee"]);
# print("balance: " + result["data"]["balance"]);

sys.exit(0);

