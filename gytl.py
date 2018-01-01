# -*- coding: utf-8 -*-

from gmsdk.api import StrategyBase
import datetime
import time
import talib as tbs
import statsmodels.api as sm
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

class Mystrategy(StrategyBase):

    def __init__(self, *args, **kwargs):
        super(Mystrategy, self).__init__(*args, **kwargs)
        self.long = False
        self.short = False
        self.first_subject = 'SZSE.300618'
        self.second_subject= 'SHSE.603799'

    def on_login(self):
        pass

    def analysis_pair(self,first_subject, second_subject):
        # p equal to ZN, y equal to CU
        #  get subject_data
        # history
        # cu equal to first
        # zn equal to second
        CU_data = self.get_last_n_bars(first_subject,60,500)
        CU88_close = [key.close for key in CU_data]
        #print(len(CU88_close))
        #CU88_close = CU_data[['close', 'bob']]
        # CU88_close_1d = history(symbol=first_subject, frequency='1d', start_time=start_date,end_time=end_date,df=True)
        # CU88_close_1d = CU88_close_1d['close']
        # print(Y88)
        ZN_data = self.get_last_n_bars(second_subject,60,500)
        # print(ZN_data)
        # print(CU_data)
        ZN88_close = [key.close for key in ZN_data]
        if len(ZN88_close) != len(CU88_close):
            print('errer%d %d ' %(len(CU88_close),len(ZN88_close)))
        # ZN88_close_1d = history(symbol=first_subject, frequency='1d', start_time=start_date,end_time=end_date,df=True)
        # ZN88_close_1d = ZN88_close_1d['close']
        # ZN88_open= ZN_data['open']
        # ZN88= (ZN88_open -ZN88_close)/ZN88_open
        # print(ZN88_close)
        # print(len(ZN88_close.tolist()),len(CU88_close.tolist()))
        #ZN88_close.index = ZN88_close['bob']
        #CU88_close.index = CU88_close['bob']
        PY = pd.DataFrame()
        #PY = pd.merge(ZN88_close, CU88_close)
        PY['CU88_close'] = CU88_close
        PY['ZN88_close'] = ZN88_close
        #del PY['close_x']
        #del PY['close_y']
        # PY.index = PY['bob']
        # PY=pd.DataFrame([ZN88_close.tolist(),CU88_close.tolist()],
        #                index=['ZN88_close','CU88_close']).T
        # x is second subject, zn
        # y is first subject. cu
        # PY_1d = pd.DataFrame([list(CU88_close_1d),list(ZN88_close_1d)],index=['CU88_close_1d','ZN88_close_1d']).T
        # print(PY)
        #X = PY.ZN88_close.values
        #y = PY.CU88_close.values
        # print('dddddd',X)
        # print(PY)
        #model = sm.OLS(y, X)
        #results = model.fit()
        # 画出两个合约的走势图
        # PY['ZN88_close*'+str(results.params)]= PY['ZN88_close']*results.params
        PY['spread_60s'] = PY['CU88_close'] - PY['ZN88_close']  # +str(results.params)]
        # PY_1d['spread_1d']=PY_1d['CU88_close_1d']-PY_1d['ZN88_close_1d']
        # PY_1d['spread_1d']=PY_1d['spread_1d']-PY_1d['spread_1d'].mean()
        #print(PY)
        # 计算价差
        # spread = close_rb[:-1] - close_hc[:-1]
        # 计算布林带的上下轨
        # PY['up60s'] = np.mean(PY['spread_60s']) + 2 * np.std(PY['spread_60s'])
        # PY['down60s'] = np.mean(PY['spread_60s']) - 2 * np.std(PY['spread_60s'])
        # PY['up1d'] = np.mean(PY_1d['spread_1d']) + 2 * np.std(PY_1d['spread_1d'])
        # PY['down1d'] = np.mean(PY_1d['spread_1d']) - 2 * np.std(PY_1d['spread_1d'])
        # 计算最新价差
        # spread_now = close_rb[-1] - close_hc[-1]
        return PY
    def on_error(self, code, msg):
        pass

    def on_tick(self, tick):
        pass

    def on_execrpt(self, res):
        pass

    def on_order_status(self, order):
        pass

    def on_order_new(self, res):
        pass

    def on_order_filled(self, res):
        pass

    def on_order_partiall_filled(self, res):
        pass

    def on_order_stop_executed(self, res):
        pass

    def on_order_canceled(self, res):
        pass

    def on_order_cancel_rejected(self, res):
        pass
    def on_bar(self, bar):
        # spread 是 first - second
        # second 603799 华友钴业 800
        # first 300618 寒锐钴业 235
        # 向上突破，是 价格要上升。 第一个要上涨，第二个要下跌。
        # 价差向下突破，是 第一个价格要下降，第二个价格要上升。

        PY = self.analysis_pair(self.first_subject,self.second_subject)
        PY['spread_ema500'] = tbs.EMA(np.array(PY['spread_60s']), 400)
        PY['spread_ema100'] = tbs.EMA(np.array(PY['spread_60s']), 100)
        #print(PY.tail(2))
        #print('spread')
        if PY.iloc[-1,4] > PY.iloc[-1,3] and self.long == False:
            self.open_long(self.first_subject[:4],self.first_subject[5:],0,1000)
            self.close_long(self.second_subject[:4],self.second_subject[5:],0,500)
            self.long = True
            self.short = False
            print('open long positions%s %s %d' %(self.first_subject[:4],self.first_subject[5:],1000))
        elif PY.iloc[-1,4] < PY.iloc[-1,3] and self.short == False:
            self.open_long(self.second_subject[:4], self.second_subject[5:], 0, 500)
            self.close_long(self.first_subject[:4], self.first_subject[5:], 0, 1000)
            self.long = False
            self.short = True
            print('open long positions%s %s %d' %(self.second_subject[:4],self.second_subject[5:],1000))
if __name__ == '__main__':
    myStrategy = Mystrategy(
        username='13021932357',
        password='123zhezheyjq',
        strategy_id='15ef9373-ec90-11e7-ada5-c45444fb39a9',
        subscribe_symbols='SHSE.603799.bar.600, SZSE.300618.bar.600',
        mode=4,
        td_addr=''
    )
    myStrategy.backtest_config(
        start_time='2017-12-10 08:05:00',
        end_time='2017-12-20 20:00:00',
        initial_cash=1000000,
        transaction_ratio=0.5,
        commission_ratio=0.0001,
        slippage_ratio=0.0001,
        price_type=1)
    ret = myStrategy.run()
    print('exit code: ',myStrategy.get_strerror(ret))