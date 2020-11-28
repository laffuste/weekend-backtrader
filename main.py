from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

import backtrader as bt
import backtrader.analyzers as btanalyzers

import settings
from strategy.turtle import TurtleStrategy

from os import listdir

from os.path import isfile, join

DATA_FEED_PATH = 'data\\feed\\'
DATA_SUFFIX = '.csv'


def _load_datafeed(cerebro: bt.Cerebro):
    """Load all feeds into backtrader"""

    # Datas are in a subfolder of the samples. Need to find where the script is located
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))

    feeds = [f for f in listdir(DATA_FEED_PATH) if isfile(join(DATA_FEED_PATH, f)) and DATA_SUFFIX in f]

    for feed in feeds:
        data_path = os.path.join(modpath, f'{DATA_FEED_PATH}{feed}')

        # Data Feed
        data = bt.feeds.YahooFinanceCSVData(
            dataname=data_path,
            # DO NOT PASS VALUES BEFORE THIS DATE
            fromdate=settings.FROM_DATE,
            # DO NOT PASS VALUES AFTER THIS DATE
            todate=settings.TO_DATE,
            reverse=False)

        cerebro.adddata(data)
    print(f"Added {len(feeds)} data feeds files")


def _print_summary(thestrat):
    print()
    print('============ Summary ================')
    print('Sharpe Ratio: ', thestrat.analyzers.mysharpe.get_analysis()['sharperatio'])
    print('Annual returns\n   ',
          "\n    ".join([f'{year}: {ret}' for year, ret in thestrat.analyzers.annualret.get_analysis().items()]))
    print('Total returns\n   ',
          "\n    ".join([f'{year}: {ret}' for year, ret in thestrat.analyzers.returns.get_analysis().items()]))
    print('=====================================')


def execute_backtest():
    cerebro = bt.Cerebro()

    # Strategy
    strats = cerebro.addstrategy(TurtleStrategy)

    # Analyser
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='mysharpe')
    cerebro.addanalyzer(btanalyzers.AnnualReturn, _name='annualret')
    cerebro.addanalyzer(btanalyzers.Returns, _name='returns')

    _load_datafeed(cerebro)

    # Initial Cash
    cerebro.broker.setcash(100000.0)
    # Comission
    cerebro.broker.setcommission(commission=0.001)

    # Run backtest
    print("Initializing backtest,this will take few moments...")
    strats = cerebro.run()

    # Summary
    _print_summary(strats[0])


if __name__ == '__main__':
    execute_backtest()
