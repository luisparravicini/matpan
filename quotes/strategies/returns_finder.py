import pandas as pd


class ReturnsFinder:
    def __init__(self, signals):
        self.positions = pd.DataFrame(index=signals.index).fillna(0)

    def update(self, signals):
        signals['position'] = signals['signal'].diff()
        price = signals['price']

        initial_capital = 1000000
        shares = 1000
        self.positions['position'] = shares * signals['signal']
        portfolio = self.positions.multiply(price, axis=0)

        pos_diff = portfolio.diff()

        portfolio['holdings'] = (self.positions.multiply(price, axis=0)).sum(axis=1)
        portfolio['cash'] = initial_capital - (pos_diff.multiply(price, axis=0)).sum(axis=1).cumsum()
        portfolio['total'] = portfolio['cash'] + portfolio['holdings']
        portfolio['returns'] = portfolio['total'].pct_change()

        # print(portfolio.tail())
        value = portfolio['total'].tail(1).values[0]
        total_return = ((value / initial_capital) - 1) * 100
        # print(f'value: ${value:.2f}, total returns: {total_return:.2f}%')

        return (value, total_return)
