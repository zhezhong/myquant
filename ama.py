# -*- coding: utf-8 -*-

from gmsdk.api import StrategyBase
from gmsdk.api import StrategyBase
import datetime
import time
import talib as tbs
import statsmodels.api as sm
import pandas as pd
import numpy as np
from scipy.stats import linregress
import pandas

class Mystrategy(StrategyBase):
    def __init__(self, *args, **kwargs):
        super(Mystrategy, self).__init__(*args, **kwargs)

        self.EffRatioLength1 = 10
        self.FastAvgLength1 = 2
        self.SlowAvgLength1 = 30

        self.EffRatioLength2 = 20
        self.FastAvgLength2 = 4
        self.SlowAvgLength2 = 60
        self.symbol = 'SZSE.000001'
        # self.total_asset = 10000000
        self.init = True
        # unit_v = int(0.5 * float(self.total_asset))

        self.long = False
        self.short = False

    # def caculate sensititive AMA
    def KAMA(self,price, n=10, pow1=2, pow2=30):
        ''' kama indicator '''
        ''' accepts pandas dataframe of prices '''

        absDiffx = abs(price - price.shift(1))
        # direction
        ER_num = abs(price - price.shift(n))
        # votility
        ER_den = pandas.stats.moments.rolling_sum(absDiffx, n)
        # efficient ratio
        ER = ER_num / ER_den
        # efficient
        sc = (ER * (2.0 / (pow1 + 1) - 2.0 / (pow2 + 1.0)) + 2 / (pow2 + 1.0)) ** 2.0

        answer = np.zeros(sc.size)
        N = len(answer)
        first_value = True

        for i in range(N):
            #print('------',sc)
            if sc[i] != sc[i]:
                answer[i] = np.nan
            else:
                if first_value:
                    answer[i] = price[i]
                    first_value = False
                else:
                    answer[i] = answer[i - 1] + sc[i] * (price[i] - answer[i - 1])
        return answer


    def on_tick(self, tick):
        pass

    def on_bar(self, bar):
        if self.init:
            self.open_long(self.symbol[:4], self.symbol[5:], price=0, volume=5000)
            postion = self.get_position(self.symbol[:4], self.symbol[5:], 1)
            #print('ddd', postion.volume)
            self.init=False
        #self.last_price = self.get_last_n_ticks(self.symbol,1)[0].last_price
        etime = bar.strendtime[:10]+' '+bar.strendtime[11:19]
        #print(etime)

        n_bar = self.get_last_n_bars(self.symbol, 300, 400, end_time=etime)
        # print(n_bar[0].close)
        # print(n_bar[1].close)
        data= pd.DataFrame()
        data['close'] = list([key.close for key in n_bar])
        #print(type(data['close']))

        AMA1 = self.KAMA(data['close'], self.EffRatioLength1, self.FastAvgLength1, self.SlowAvgLength1)
        AMA2 = self.KAMA(data['close'], self.EffRatioLength2, self.FastAvgLength2, self.SlowAvgLength2)
        spread = AMA1 - AMA2
        #print(etime, 'AMA1',AMA1[-1],'AMA2',AMA2[-1])

        # 原假设一天 开多仓不超过5次。
        # unit_v = int(0.1*float(self.total_asset)/float(self.last_price))
        # print(sma_5[-1],'====;',sma_10[-1])
        # 20日均线向上，平多不开空，目前处于多头行情中。
        # print(range(3))
        # print(sma_20[-3:])
        #rg = linregress(range(5), sma_20[-5:] - sma_20[-5:].mean())
        #print(rg[0], etime, sma_20[-5:])

        # MACD RSI 追击判断
        # 在强势下跌过程中，不做多
        print(len(AMA1)),len(AMA2)
        # 赚钱之后不要立马想着还有另外的赚钱机会，赚钱之后屏蔽40个单位的出入场信号。

        # 向上突破建仓的问题:
        # 向上将要交叉间隔 0.2%，如果当前价格在10日均线之上1% 基本确定，会出现交叉，提前买入。
        # 如果交叉时候，前面很长一段时间都没有促发 交易信号。出现突破。则交易。
        # 如果交叉的时候，刚刚结束大下跌行情， 而此时交叉时候，信号已经站在10日均线上方很久了。这个就是震荡信号。
        #获取上一个Roderick
        # 如果三十个小交易日 波动幅度都很小，一旦突破，长期持有30个交易日。
        #布林带很窄的时候，触发的交易信号要入， 布林带很宽的时候，触发的交易信号，保守一点。
        #def caculate_profit(self):

        if(len(AMA1)!=0 and len(AMA2)!=0):
            if AMA1[-1]>AMA2[-1]  and self.long == False :
                self.long = True
                #self.long_price =
                self.open_long(self.symbol[:4], self.symbol[5:], price=0, volume=1000)
                self.short = False
                self.long_price = self.price
                print('open long positions%s %s %d' % (self.symbol[:4], self.symbol[5:], 2000))
                # 强势上涨过程中不做空。
            elif AMA1[-1] < AMA2[-1] and self.short == False :
                self.long = False
                self.close_long(self.symbol[:4], self.symbol[5:], price=0, volume=1000)
                self.short = True
                self.short_price = self.price
                print('open short positions%s %s %d' % (self.symbol[:4], self.symbol[5:], 2000))

    def on_execrpt(self, res):
        pass

    def on_order_new(self, res):
        pass
    def on_tick(self,tick):
        self.price = tick.last_price
        print(self.price)
        pass



if __name__ == '__main__':
    myStrategy = Mystrategy(
        username='13021932357',
        password='123zhezheyjq',
        strategy_id='17d3e97e-ed2f-11e7-8b08-c45444fb39a9',
        subscribe_symbols='SZSE.000001.tick,SZSE.000001.bar.300',
        mode=4,
        td_addr=''
    )
    myStrategy.backtest_config(
        start_time='2017-01-01 08:00:00',
        end_time='2017-12-31 21:25:00',
        initial_cash=100000,
        transaction_ratio=0.8,
        commission_ratio=0.004,
        slippage_ratio=0.0001,
        price_type=1)
    ret = myStrategy.run()
    print('exit code: ', ret)