import backtrader as bt
from backtrader.sizers import PercentSizer

from settings import INDEX_TICKER


class TurtleStrategy(bt.Strategy):
    params = (
        ('maperiod', 15),
        ('breakout_period_days', 100),
        ('price_rate_of_change_perc', 0.3),
        ('regime_filter_ma_period', 200),
        ('trailing_stop_loss_perc', 0.2),
        ('trade_alloc_perc', 0.05),
        ('printlog', True)
    )

    def log(self, txt, dt=None, doprint=False):
        """Logging function fot this strategy"""
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # keep track of pending orders and buy price/commission
        self.orders = []
        self.stop_losses = []
        self.buyprice = None
        self.buycomm = None
        self.symbols_held = set()

        # FIXME: double check this, is it really sizing correctly?
        sizer = PercentSizer()
        sizer.params.percents = self.params.trade_alloc_perc * 100
        self.setsizer(sizer)

        # Add a MovingAverageSimple indicator
        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.maperiod)

        # find index (benchmark)
        self.index_data = self.getdatabyname(INDEX_TICKER)
        self.sma_index = bt.indicators.SimpleMovingAverage(self.index_data, period=self.params.regime_filter_ma_period)

    def _is_bull_regime(self):
        # print(f"{self.index_data[0]} > {self.sma_index[0]} ? {self.index_data[0] > self.sma_index[0]}")
        return self.index_data[0] > self.sma_index[0]

    def _is_instrument_held(self, data_feed):
        """
        Do we have a (executed or pending) position on the instrument
        """
        return data_feed._name in self.symbols_held

    def _next_symbol(self, data_feed):
        past_price = data_feed.close[-self.params.breakout_period_days]
        yesterdays_price = data_feed.close[-1]  # yesterday: avoid lookahead bias
        if yesterdays_price == 0:
            # TODO: clean data, some close prices are zero
            # avoid a bug (division by zero): data unclean
            return
        rate_of_change = (yesterdays_price - past_price) / yesterdays_price

        if rate_of_change > self.params.price_rate_of_change_perc and not self._is_instrument_held(data_feed):
            # instrument breakout

            # buy order
            buy_order = self.buy(data=data_feed, exectype=bt.Order.Market)
            self.orders.append(buy_order)

            # stop loss
            sell_order = self.sell(parent=buy_order, exectype=bt.Order.StopTrail,
                                   trailpercent=self.params.trailing_stop_loss_perc)
            self.stop_losses.append(sell_order)
            # keep track of symbols held: we want one position per symbol max
            self.symbols_held.add(data_feed._name)

            self.log(
                f'Buy Order sent ({buy_order.ref} / stoploss: {sell_order.ref}): {data_feed._name}, rate of change: {int((rate_of_change * 100))}% (ref price: {past_price}, yesterdays close: {yesterdays_price}) ')

    def _is_last_bar(self):
        return len(self.data) == self.data.buflen() - 1

    def _close_positions(self):
        self._debug_position()
        open_positions = self._get_open_positions()
        self.log(
            f">>> Closing ALL ({len(open_positions)}) positions: {[f' {n}: {p.size}' for n, p in open_positions.items()]}")
        for name, _ in open_positions.items():
            # self.close(data=pos, size=pos.size())
            self.close(data=self.getdatabyname(name))
        # for stop_loss in self.stop_losses if stop_loss == 1:
        alive_stop_losses = [stop_loss for stop_loss in self.stop_losses if stop_loss.alive()]
        self.log(
            f">>> Cancelling ALL ({len(alive_stop_losses)}) stop losses.")
        for stop_loss in alive_stop_losses:
            stop_loss.cancel()

    def next(self):
        self.log('Close: %.2f' % self.index_data.close[0])

        if self._is_last_bar():
            self._close_positions()
            return

        if self._is_bull_regime():  # regime filter
            for data in self.datas:
                if data._name == self.index_data._name:
                    # skip index
                    continue
                self._next_symbol(data)

    def notify_order(self, order):

        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'Buy Order executed (%s): %s, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.ref, order.params.data._name, order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('Sell Order executed (%s): %s, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.ref, order.params.data._name, order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.log(f'> Open positions: {len(self._get_open_positions())}, remaining cash: {self.broker.cash}')

            # self._debug_position()

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'Order {order.ref} {order.getstatusname()}')
            self.log(f'> Open positions: {len(self._get_open_positions())}, remaining cash: {self.broker.cash}')

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT (%s), GROSS %.2f, NET %.2f' %
                 (trade.ref, trade.pnl, trade.pnlcomm))

    def _get_open_positions(self) -> dict:
        positions_tuple = [(d._name, self.getposition(d)) for d in self.datas]
        return {n: p for (n, p) in positions_tuple if p.size > 0}

    def _debug_position(self):
        curr_pos = self._get_open_positions()
        curr_post_na = 'N/A' if len(curr_pos) == 0 else ''
        print(f'Current positions: {curr_post_na}')
        for name, pos in self._get_open_positions().items():
            print(f'      {name}: {pos.size:.2f} @ {pos.price}')

    def stop(self):
        self.log(f'> Open positions: {len(self._get_open_positions())}, remaining cash: {self.broker.cash}')

        # self._debug_position()

        self.log('(MA Period %2d) Ending Value %.2f' %
                 (self.params.maperiod, self.broker.getvalue()), doprint=True)
