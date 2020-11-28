import datetime

# start date of the backtest (will also filter out market data)
FROM_DATE = datetime.datetime(2015, 1, 1)
# end date of the backtest (will also filter out market data)
TO_DATE = datetime.datetime(2019, 12, 30)

# Local file for All Ords symbols (ASX 500) -> https://www.allordslist.com/
ALL_ORDS_CSV = '20200601-all-ords.csv'
# Local file for ASX 100 -> https://www.asx100list.com/
ASX100_CSV = '20200601-asx100.csv'

INDEX_TICKER = '^AORD'
