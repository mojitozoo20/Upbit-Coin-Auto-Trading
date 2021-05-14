import pyupbit
import numpy as np
TICKER = 'KRW-QTUM'
INTERVAL = 'minute30'

def get_ror(k=0.5):
    df = pyupbit.get_ohlcv(TICKER, INTERVAL, 200, period=0.1)

    df['ma5'] = df['close'].rolling(5).mean().shift(1)
    df['ma10'] = df['close'].rolling(10).mean().shift(1)
    df['ma15'] = df['close'].rolling(15).mean().shift(1)
    df['ma50'] = df['close'].rolling(50).mean().shift(1)

    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)

    #df['bull'] = (df['ma5'] > df['ma10']) & (df['ma10'] > df['ma15']) & (df['ma15'] > df['ma50'])
    df['bull'] = df['open'] > df['ma5']

    fee = 0.0032  # 수수료

    df['ror'] = np.where((df['high'] > df['target']) & df['bull'], df['close'] / df['target'] - fee, 1)

    ror = df['ror'].cumprod()[-2]
    return ror

print(f'<<{TICKER} {INTERVAL}>>')
print('k값   수익률')
for k in np.arange(0.1, 1.0, 0.1):
    ror = get_ror(k)
    print("%.1f %f" % (k, ror))
