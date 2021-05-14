import pyupbit
import numpy as np
YEAR = '2021'
KVALUE = 0.5
MA_ = 15


def get_hpr(ticker):
    try:
        df = pyupbit.get_ohlcv(ticker)
        df = df.loc[YEAR]  # 해당 년도의 수익률 TOP5 코인 검색

        df['ma5'] = df['close'].rolling(MA_).mean().shift(1)
        df['range'] = (df['high'] - df['low']) * KVALUE
        df['target'] = df['open'] + df['range'].shift(1)
        df['bull'] = df['open'] > df['ma5']

        fee = 0.001
        df['ror'] = np.where((df['high'] > df['target']) & df['bull'],
                             df['close'] / df['target'] - fee,
                             1)

        df['hpr'] = df['ror'].cumprod()
        df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        return df['hpr'][-2]
    except:
        return 1


tickers = pyupbit.get_tickers(fiat='KRW')

hprs = []
for ticker in tickers:
    hpr = get_hpr(ticker)
    hprs.append((ticker, hpr))

sorted_hprs = sorted(hprs, key=lambda x: x[1])

print(YEAR, '년도의 TOP5 원화거래소 종목')
print(sorted_hprs[-5:])
