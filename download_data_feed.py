import time

import pandas as pd
import pandas_datareader as pdr

import settings

# for dev purposes, don't download all symbols to avoid hitting the limit
MAX_DOWNLOADS = None


def _download_from_yahoo(symbol: str):
    """Downloads a symbol from yahoo and drops it in /data/feed"""
    stock_data = pdr.get_data_yahoo(symbols=symbol,
                                    start=settings.FROM_DATE,
                                    end=settings.TO_DATE,
                                    adjust_price=False,
                                    interval='d')
    # clean adjusted closes of 0 (insert last available val)
    stock_data['Adj Close'].replace(to_replace=0, method='ffill')
    columns_order = ['Open', 'High', 'Low', 'Close', 'Adj Close',
                     'Volume']  # need to be explicit, pandas messes up the order

    # don't save when the earliest market data is later than the begining of our test (backtrader breaks)
    min_date = stock_data.index.min()
    if min_date > settings.FROM_DATE:
        print(f'Instrument {symbol} skipped: it\'s min date ({min_date}) is later than the min date of the test ({settings.FROM_DATE})')
        return False
    # don't save when the latest market data is earlier than the end of our test (backtrader breaks)
    max_date = stock_data.index.max()
    if max_date > settings.TO_DATE:
        print(f'Instrument {symbol} skipped: it\'s max date ({max_date}) is earlier than the min date of the test ({settings.TO_DATE})')
        return False
    stock_data.to_csv(f'data\\feed\\{symbol}.csv', columns=columns_order)
    return True


def _find_candidate_symbols():
    """
    Returns symbols from index files: ALL_ORDS_CSV and ASX100_CSV
    """
    all_ords = pd.read_csv(f'data\{settings.ALL_ORDS_CSV}', header=1)
    asx100 = pd.read_csv(f'data\{settings.ASX100_CSV}', header=1)

    all_ords_codes = list(all_ords['Code'])
    print(f"Found {len(all_ords_codes)} all ords (ASX500) symbols.")

    asx_codes = set(asx100['Code'])
    print(f"Found {len(asx_codes)} ASX 100 symbols.")

    return [s for s in all_ords_codes if s not in asx_codes]


def _download_index():
    """Download the index data to be used as benchmark"""
    _download_from_yahoo('^AORD')


def _download_data(candidate_symbols: list):
    start = time.time()  # What in other posts is described is
    num_download = 0
    for symbol in candidate_symbols:
        asx_symbol = f'{symbol}.AX'
        try:
            downloaded = _download_from_yahoo(asx_symbol)
            if downloaded:
                num_download =+ 1
            print('.', end='')
            time.sleep(0.25)  # don't flood yahoo
        # except pdr._utils.RemoteDataError as e:
        except Exception as e:
            print(f"Error while downloading: {asx_symbol}. This symbol might not be listed in yahoo? ({e})")
    print('.')
    total_seconds = (time.time() - start)
    print(
        f"Downloaded {num_download} (out of {len(candidate_symbols)}) in {total_seconds:.2f}s (~{total_seconds / num_download:.2f}s per symbol).")


def download_feed_data():
    """
    Download necessary feeds.
    """
    _download_index()
    candidate_symbols = _find_candidate_symbols()
    if MAX_DOWNLOADS:
        # download a limited subset
        candidate_symbols = candidate_symbols[:MAX_DOWNLOADS]

    print(f"Downloading {len(candidate_symbols)} small cap symbols (in ASX500 but not in ASX100). "
          f"This might take a while...")
    _download_data(candidate_symbols)


if __name__ == '__main__':
    download_feed_data()
