# -*- coding: utf-8 -*-

from gmsdk.api import StrategyBase
import datetime
import time
import talib as tbs
import statsmodels.api as sm
import pandas as pd
import numpy as np
from scipy.stats import linregress
import matplotlib.pyplot as plt
#from function_tool import *
pd.set_option('precision', 5)

class Mystrategy(StrategyBase):
    def __init__(self, *args, **kwargs):
        super(Mystrategy, self).__init__(*args, **kwargs)
        self.symbol = 'SZSE.000001'
        #self.total_asset = 10000000
        self.init = True
        #unit_v = int(0.5 * float(self.total_asset))
        self.order_list =[]
        self.long = False
        self.short = False
        self.unit_volume = 3000
        self.start_time = '2017-12-20 08:05:00'
        self.boll_threshold=0.01
        # 千分之一的扰动很正常。至少得千分之1.6
        self.sma_threshold=0.0016
        self.profit_threhold=0.02

    # def caculate sensititive AMA
    def KAMA(price, n=10, pow1=2, pow2=30):
        ''' kama indicator '''
        ''' accepts pandas dataframe of prices '''

        absDiffx = abs(price - price.shift(1))


        ER_num = abs(price - price.shift(n))
        ER_den = pandas.stats.moments.rolling_sum(absDiffx, n)
        ER = ER_num / ER_den
        sc = (ER * (2.0 / (pow1 + 1) - 2.0 / (pow2 + 1.0)) + 2 / (pow2 + 1.0)) ** 2.0
        answer = np.zeros(sc.size)
        N = len(answer)
        first_value = True

        for i in range(N):
            if sc[i] != sc[i]:
                answer[i] = np.nan
            else:
                if first_value:
                    answer[i] = price[i]
                    first_value = False
                else:
                    answer[i] = answer[i - 1] + sc[i] * (price[i] - answer[i - 1])
        return answer
    def stop_profit(self):
        if self.long:
            if self.price > self.long_buy_price*(1+self.profit_threhold):
                self.close_long(self.symbol[:4], self.symbol[5:], price=self.price, volume=self.unit_volume)
                print('close long profit positions%s %s volume:%d at price:%f long buy price %f' % (
                self.symbol[:4], self.symbol[5:], self.unit_volume, self.price, self.long_buy_price))
                self.long = False
                self.long_sell_price = self.price
        if self.short:
            if self.price <self.short_buy_price*(1-self.profit_threhold):
                self.open_long(self.symbol[:4], self.symbol[5:], price=self.price, volume=self.unit_volume)
                print('close short profit  positions%s %s volume:%d at price:%f short buy price %f' % (
                    self.symbol[:4], self.symbol[5:], self.unit_volume,self.price, self.short_buy_price))
                self.short = False
                self.short_sell_price = self.price

    # 2017年 8月 10 明明那一拨行情有5%的利润，你特么 2% 就止盈了，还是不是接下来3%的利润蒸发了。
    #  这是第一笔亏损。
    def on_tick(self, tick):
        if (tick.last_price != 0):
            self.price = tick.last_price
        #self.stop_profit()
    def on_bar(self, bar):
        if self.init:
            self.open_long(self.symbol[:4], self.symbol[5:], price=0, volume=5000)
            self.long_buy_price = self.price
            postion = self.get_position(self.symbol[:4], self.symbol[5:], 1)
            #print('ddd', postion.volume)
            self.init=False
        #print(bar.strendtime)
        etime = bar.strendtime[:10]+' '+bar.strendtime[11:19]
        n_bar = self.get_last_n_bars(self.symbol,300,100,end_time=etime)
        #print(type(n_bar))
        # 我知道什么是reverse 本身了。
        n_bar.reverse()
        #print(type(n_bar))
        data = pd.DataFrame()
        data['data']  = [key.close for key in n_bar]
        data['close'] = [key.close for key in n_bar]
        data['low']   = [key.low for key in n_bar]
        data['high']  = [key.high for key in n_bar]
        data['strendtime']=[key.strendtime for key in n_bar]
        #print(len(data['close']))
        if (len(data['high']))== 0:

            return 0
        #print(data)
        # 用分钟级别数据，获取五分钟 数据的 5单位均线
        atr = tbs.ATR(np.array(data['high']),np.array(data['low']),np.array(data['close']),20)

        sma_5 = tbs.EMA(np.array(data['close']),5)
        # 10 单位五分钟均线
        sma_10 = tbs.EMA(np.array(data['close']), 20)
        # 20单位 五分钟均线
        sma_20 = tbs.EMA(np.array(data['close']),20)
        plt.plot(sma_20)

        # 获取 布林带
        upper, middle, lower = tbs.BBANDS(np.array(data['data']), timeperiod=10,nbdevup=2,nbdevdn=2,matype=tbs.MA_Type.SMA)
        boll_width = upper - lower
        #原假设一天 开多仓不超过5次。
        #unit_v = int(0.1*float(self.total_asset)/float(self.last_price))
        #print(sma_5[-1],'====;',sma_10[-1])
        # 20日均线向上，平多不开空，目前处于多头行情中。
        #print(range(3))
        #print(sma_20[-3:])
        rg = linregress(range(5), sma_20[-5:])
        #print(rg[0],etime ,sma_20[-5:])
        #self.backtest_config.start_time
        # MACD RSI 追击判断
        # 在强势下跌过程中，不做多
        # print(len(AMA1), len(AMA2))
        # 赚钱之后不要立马想着还有另外的赚钱机会，赚钱之后屏蔽40个单位的出入场信号。
        # 向上突破建仓的问题:
        # 向上将要交叉间隔 0.2%，如果当前价格在10日均线之上1% 基本确定，会出现交叉，提前买入。
        # 如果交叉时候，前面很长一段时间都没有促发 交易信号。出现突破。则交易。
        # 如果交叉的时候，刚刚结束大下跌行情， 而此时交叉时候，信号已经站在10日均线上方很久了。这个就是震荡信号。
        # 获取上一个Roderick
        # 如果三十个小交易日 波动幅度都很小，一旦突破，长期持有30个交易日。
        # 布林带很窄的时候，触发的交易信号要入， 布林带很宽的时候，触发的交易信号，保守一点。
        # 布林带达到历史30日最低值。如果有均线突破，则开仓
        # 布林带很宽的时候，并且均线较近，不做调仓信号。
        # 已经盈利后有一个不亏的止盈线。
        # def caculate_profit(self):
        # MACD RSI 追击判断
        # 在强势下跌过程中，不做多开仓。
        if sma_5[-1] > sma_10[-1] and self.long == False and rg[0]>-0.005 :
            #平 空 仓
            if(self.short):
                self.short = False
                self.open_long(self.symbol[:4],self.symbol[5:],price=self.price, volume= self.unit_volume)
                self.short_sell_price = self.price
                print(etime,'close short  positions%s %s volume:%d at price:%f sma5:%f sma10:%f' %(self.symbol[:4], self.symbol[5:], self.unit_volume,self.price, sma_5[-1], sma_10[-1]))

            # 开多仓需要追加一些条件。
            # 1. rg[0]>-0.01 强势下跌 不做多。
            # 2. 前面波动太大真实波动幅度太大，不做多。
            # 3. 前面已经赚了一大笔 空单的钱，不做多，因为趋势过后一般横盘。（后续可以做短期单）
            # 4.
            '''
            orders = self.get_orders_by_symbol(self.symbol[:4], self.symbol[5:], self.start_time, etime)
            self.last_long_order.buy_price
            self.last_long_order.sell_price
            self.last_short_order.buy_price
            self.last_short_order.sell_price
            self.last_short_order.amount
            self.last_long_order.amount
            for order in orders:
                print(order.sending_time)
           '''

            if sma_5[-1] < (sma_10[-1]*(1+self.sma_threshold)) or rg[0]<-0.008 or boll_width[-1] > self.boll_threshold*self.price:
                pass
            else:
                print('---------------', etime)
                print('sma20 slope is:%d and bollwidth is:%f,thre is%f' %(rg[0], boll_width[-1], self.boll_threshold * self.price))

                # 开多仓
                self.long = True
                print('open long positions%s %s volume:%d price:%f sma5:%f sma10:%f' %(self.symbol[:4], self.symbol[5:], self.unit_volume,self.price,sma_5[-1], sma_10[-1]))
                self.open_long(self.symbol[:4], self.symbol[5:], price=self.price, volume=self.unit_volume)
                self.long_buy_price = self.price
            #强势上涨过程中不做空。

        elif sma_5[-1] < sma_10[-1] and self.short == False and rg[0]<0.005:
            # 先平多仓
            #

            if self.long:
                self.long = False
                self.long_sell_price = self.price
                self.close_long(self.symbol[:4],self.symbol[5:],price=self.price, volume= self.unit_volume)
                print(etime,'close long positions%s %s volume:%d price: %f ,sma5:%f sma10:%f' % (self.symbol[:4], self.symbol[5:], self.unit_volume,self.price, sma_5[-1], sma_10[-1]))
            #if len(orders)<5:
            #    self.last_order_judge = True
            #else:
            #    # todo
            #    self.last_order_judge = False

            # 1. rg[0]>0.008 强势上涨 不做多。
            # 2. 前面波动太大真实波动幅度太大，不做空，，就是 波动幅度太大，处于强烈震荡期，那么就不操作，赚手续费。2% 以内的价格波动不操作。。
            # 3. 前面已经赚了一大笔 多头的钱，可以做空，涨后一般可以跌，因为趋势过后一般横盘。（后续可以短期)
            # 4.
            if sma_5[-1] > (sma_10[-1]*(1-self.sma_threshold)) or rg[0] > 0.008 or boll_width[-1] > self.boll_threshold * self.price:
                pass
            else:
                print('-----------', etime)
                print('sma20 slope is:%f and boll width is:%f,thre is%f, ' % (rg[0], boll_width[-1], self.boll_threshold * self.price))

                # 再开空仓；
                # 上升行情中，rg[0] = self.
                new_order = self.close_long(self.symbol[:4], self.symbol[5:], price=self.price, volume=self.unit_volume)
                self.short = True
                self.short_buy_price = self.price
                #print(new_order)
                print('open short positions%s %s volume:%d at price: %f ,sma5:%f sma10:%f' %(self.symbol[:4],self.symbol[5:],self.unit_volume,self.price,sma_5[-1],sma_10[-1]))










if __name__ == '__main__':
    myStrategy = Mystrategy(
        username='13021932357',
        password='123zhezheyjq',
        strategy_id='dcc838a8-ecbb-11e7-8b08-c45444fb39a9',
        subscribe_symbols='SZSE.000001.tick,SZSE.000001.bar.300',
        mode=4,
        td_addr='127.0.0.1:8001'
    )
    myStrategy.backtest_config(
        start_time='2017-05-05 08:05:00',
        end_time='2017-12-20 15:05:00',
        initial_cash=100000,
        transaction_ratio=0.8,
        commission_ratio=0.0001,
        slippage_ratio=0.0001,
        price_type=0)
    ret = myStrategy.run()
    print('exit code: ', ret)