import pyupbit

TICKER = 'KRW-QTUM'
INTERVAL = 'minute30'
MA_ = 5

df = pyupbit.get_ohlcv(TICKER, INTERVAL)
close = df['close']
ma = close.rolling(MA_).mean()  # 10봉 기준 이평선 구하기
print(ma)
