import pyupbit
import numpy as np

# 테스팅할 종목 선정
TICKER = 'KRW-ETC'
INTERVAL = 'minute30'

def backtest(k = 0.5):
    # OHLCV(open, high, low, close, volume)로 당일 시가, 고가, 저가, 종가, 거래량에 대한 데이터
    df = pyupbit.get_ohlcv(TICKER, INTERVAL, 400, period=0.1)

    # 5봉 이동평균선
    df['ma5'] = df['close'].rolling(5).mean().shift(1)

    # 변동폭 = k 계산, (고가 - 저가) * k값
    #df['range'] = (df['high'] - df['low']) * KVALUE
    df['range'] = (df['high'] - df['low']) * k

    # target(매수가), range 컬럼을 한칸씩 밑으로 내림(.shift(1))
    df['target'] = df['open'] + df['range'].shift(1)

    # 상승장 여부 판단
    #df['bull'] = (df['ma5'] > df['ma10']) & (df['ma10'] > df['ma15']) & (df['ma15'] > df['ma50'])
    df['bull'] = df['open'] > df['ma5']

    fee = 0.0032  # 수수료

    # ror(수익률), np.where(조건문, 참일때 값, 거짓일때 값 np.where())
    df['ror'] = np.where((df['high'] > df['target']) & df['bull'], df['close'] / df['target'] - fee, 1)

    # 누적 곱 계산(cumprod) => 누적 수익률
    df['hpr'] = df['ror'].cumprod()

    # Draw Down 계산 (누적 최대 값과 현재 hpr 차이 / 누적 최대값 * 100)
    df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100

    # MDD 계산
    #print("MDD(%): ", df['dd'].max())

    # HPR 계산
    print(f'{TICKER} {k:.1}', "HPR: ", df['hpr'][-2])

    # 엑셀로 출력
    df.to_excel("backtesting/volatility_backtesting/result/"+TICKER+".xlsx")

print(f"<< {TICKER} {INTERVAL} >>")

for k in np.arange(0.1, 1.0, 0.1):
    backtest(k)
'''
backtest(0.5)
'''