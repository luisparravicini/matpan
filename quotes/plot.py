import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import seaborn as sns
from pandas.plotting import register_matplotlib_converters
# pip install --user
# https://github.com/matplotlib/mpl_finance/archive/master.zip
from mpl_finance import candlestick_ohlc

register_matplotlib_converters()


def plot_data(ax, start_date, end_date, quotes, series, signals, show_candlestick):
    my_year_month_fmt = mdates.DateFormatter('%Y-%m-%d')
    if show_candlestick:
        candlestick_ohlc(ax, quotes, width=0.5, colorup='g', colordown='r')

    for s in series:
        data = s[0]
        label = s[1]
        ax.plot(
            data.loc[start_date:end_date].index,
            data.loc[start_date:end_date],
            label=label
        )

    for index, value in signals.loc[start_date:end_date].iteritems():
        if value > 0:
            ax.axvline(x=index, color='green')
        if value < 0:
            ax.axvline(x=index, color='red')

    ax.legend(loc='best')
    ax.set_ylabel('$')
    ax.xaxis.set_major_formatter(my_year_month_fmt)

    # post PASO
    ax.axvline(x='2019-08-12', color='grey')


def quotes_range(date_range, quotes):
    subset = quotes.loc[date_range[0]:date_range[1]]
    return zip(
        mdates.date2num(subset.index.to_pydatetime()),
        subset['Open'],
        subset['Adj Close'],
        subset['Max'],
        subset['Min']
    )


def plot(range_dates, zoom_dates, symbol, data, series, signals):
    # sns.set(style='darkgrid', context='talk', palette='Dark2')
    fig, ax = plt.subplots(2, 1, figsize=(15, 9))
    plt.suptitle(symbol)

    quotes = quotes_range(range_dates, data)
    plot_data(
        ax[0],
        range_dates[0],
        range_dates[1],
        quotes,
        series,
        signals,
        False
    )

    quotes = quotes_range(zoom_dates, data)
    plot_data(
        ax[1],
        zoom_dates[0],
        zoom_dates[1],
        quotes,
        series,
        signals,
        True
    )

    return fig
