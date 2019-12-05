import pandas as pd


def load_data(prices_manager, start_date, end_date, symbol):
    data = prices_manager.load(symbol)
    all_weekdays = pd.date_range(start=start_date, end=end_date, freq='B')
    data = data.reindex(all_weekdays).ffill()
    return data
    # return data.loc[start_date:end_date]


def load_all_data(prices_manager, blacklist, symbols, range_dates):
    print('loading quotes')

    all_data = dict()
    for symbol in symbols:
        if symbol in blacklist:
            print(symbol, '(blacklisted)')
            continue

        data = load_data(
            prices_manager,
            range_dates[0],
            range_dates[1],
            symbol)
        close = data['Adj Close']

        if close.isnull().all():
            print(symbol, '(empty)')
            continue

        all_data[symbol] = data
        print(symbol, end="\r")

    return all_data
