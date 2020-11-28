# Weekend Backtrader

Implementation of the Weekend Trader strategy with Backtrader.


## Strategy

From Nick Radge's book "Unholy Grails" and Chat with Traders podcast: https://chatwithtraders.com/ep-178-nick-radge/

The strategy is a modification of Turtle Trading: equity long only momentum strategy. The original strategy trades on small cap industrials: australian, outside ASX 100 but inside ASX 500.   

Basic ideas:
- every trend starts with a breakout
- riding winners, cutting losers

Rules:
- only long stocks
- breakout period: 100 days (instead of 20 days)
- weekend trend trader: 20 week breakout  (break 20 week high)
- confirmation filter: Rate of Change (indicator) above a level (acceleration) i.e. -> 30 (strong breakout) percentage change price on price for the last 20 weeks
- regime filter: broader market is trending up. Underlying index trends up. Buy signal if index above SMA(200).
- trailing stop loss: 20% trailing stop -> 1% total loss in ptf per trade (0.5 * 0.2 = 0.01)
- 20 pos max, 5% capital each
- when regime filter goes from uptrend to downtrend, use 10% instead of 20% stop loss
 
 
Stats reported by Nick Radge:
- avg trading loss (single position loss) 11.97% -> 0.6% of total ptf
- avg win: 21% -> 2.6 times the loss
- win rate: 44%
- win/loss ration: 2.6
 
 

## Getting Started

1. (Optional) Create virtualenv or conda env

1. Install requirements
    ```
    pip install -r requirements.txt
    ```

1. Download data feeds:
    ```
    python download_data_feed.py 
    ```
   The symbols downloaded can be capped with MAX_DOWNLOADS const.

1. Execute Backtest
    ```
    python main.py
    ```

## Caveats

- POC, possibly there is some bug
- the backtest only runs from to  (see `main.py`'s  `_load_datafeed`)
- the feed data is not cleaned
- The data feed has survivorship bias! 
- Some symbols are ignored because there is not enough data for our timeframe
- The strategy is not profitable as it is, do not use it
- Yahoo financial download limit should be 2000 req / hour. `download_data_feed.py` will download around 378 symbols.

## Current results

```
============ Summary ================
Sharpe Ratio:  0.6201373437021387
Annual returns
    2015: 0.0
    2016: 0.4622394790766664
    2017: 1.8888994250547002
    2018: -0.22068818768678122
    2019: 0.22746678809392806
Total returns
    rtot: 1.3964532412290513
    ravg: 0.001103915605714665
    rnorm: 0.32073279810641175
    rnorm100: 32.073279810641175
=====================================
```


## See Also

- https://www.allordslist.com/
- https://www.asx100list.com/