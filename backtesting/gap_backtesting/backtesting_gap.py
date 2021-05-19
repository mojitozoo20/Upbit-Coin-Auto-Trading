import pyupbit
import plotly.graph_objects as go 
from plotly.subplots import make_subplots
import time
import pandas as pd

count_stop_loss = 0  # 손절 횟수
count_trading = 0  # 거래 횟수

def get_ohlcv(ticker):
    dfs = [ ]
    # df = pyupbit.get_ohlcv(ticker, interval="minute1", to="20210423 11:00:00")
    df = pyupbit.get_ohlcv(ticker, interval="minute1", to="20210518 23:00:00")
    dfs.append(df)

    for i in range(60):
        df = pyupbit.get_ohlcv(ticker, interval="minute1", to=df.index[0])
        dfs.append(df)
        time.sleep(0.2)

    df = pd.concat(dfs)
    df = df.sort_index()
    return df

def view_chart(df, ax_ror, ay_ror, cond_buy):
    candle = go.Candlestick(
        x = df.index,
        open = df['open'],
        high = df['high'],
        low = df['low'],
        close = df['close'],
    )

    ror_chart = go.Scatter(
        x = ax_ror,
        y = ay_ror
    )

    fig = make_subplots(specs=[ [{ "secondary_y": True }] ])
    fig.add_trace(candle)
    fig.add_trace(ror_chart, secondary_y=True)

    for idx in df.index[cond_buy]:
        fig.add_annotation(
            x = idx,
            y = df.loc[idx, 'open']
        )
    fig.show()

def short_trading_for_1percent(df):
    ma5 = df['close'].rolling(5).mean().shift(1)
    ma10 = df['close'].rolling(10).mean().shift(1)
    ma15 = df['close'].rolling(15).mean().shift(1)
    ma50 = df['close'].rolling(50).mean().shift(1)
    ma120 = df['close'].rolling(120).mean().shift(1)

    # 1) 매수 일자 판별
    cond_0 = df['high'] >= df['open'] * 1.005  # 0.5% 상승시 매수
    cond_1 = (ma15 >= ma50) & (ma50 >= ma120) & (ma15 <= ma50 * 1.03)
    cond_2 = (ma5 >= ma10) & (ma10 >= ma15)
    cond_buy = cond_0 & cond_1 & cond_2

    acc_ror = 1
    sell_date = None

    global count_stop_loss
    global count_trading
    count_stop_loss = 0  # 손절 횟수 초기화
    count_trading = 0  # 거래 횟수 초기화

    ax_ror = []
    ay_ror = []
    
    # 2) 매도 조건 탐색 및 수익률 계산
    for buy_date in df.index[cond_buy]:
        if sell_date != None and buy_date <= sell_date:
            continue

        target = df.loc[ buy_date :  ]

        cond = target['high'] >= df.loc[buy_date, 'open'] * 1.015  # 1.5% 상승시 매도
        sell_candidate = target.index[cond]

        buy_price = df.loc[buy_date, 'open'] * 1.005

        if len(sell_candidate) == 0:  # 마지막 지점 브레이크
            sell_price = df.iloc[-1, 3]
            if (sell_price / buy_price) <= 0.99:  #  하락시 손절가로 설정
                acc_ror *= 0.987
                count_stop_loss += 1
            else:
                acc_ror *= (sell_price / buy_price)
            ax_ror.append(df.index[-1])
            ay_ror.append(acc_ror)
            count_trading += 1
            break

        # 손절가 계산
        #print(target.loc[ : sell_candidate[0] ])
        stop_loss = target.loc[ : sell_candidate[0] ].iloc[0, 2]  # 매수 시점 저가 = 최저가로 설정
        for d in range(len(target.loc[ : sell_candidate[0] ])):  # 다음 매도지점 전까지 최저가격 산출
            if target.loc[ : sell_candidate[0] ].iloc[d, 2] < stop_loss:  # 최저가 산출
                stop_loss = target.loc[ : sell_candidate[0] ].iloc[0, 2]
            if d == len(target.loc[ : sell_candidate[0] ]) - 1:
                break
        
        if (stop_loss / buy_price) <= 0.99:  # 1% 하락시 손절
            sell_date = sell_candidate[0]
            acc_ror *= 0.987
            count_stop_loss += 1
            ax_ror.append(sell_date)
            ay_ror.append(acc_ror)
            count_trading += 1
            continue

        if len(sell_candidate) == 0:
            sell_price = df.iloc[-1, 3]
            if (sell_price / buy_price) <= 0.99:  # 1% 하락시 손절가 = 최종거래가
                acc_ror *= 0.987
                count_stop_loss += 1
            else:
                acc_ror *= (sell_price / buy_price)
            ax_ror.append(df.index[-1])
            ay_ror.append(acc_ror)
            count_trading += 1
            break
        else:
            sell_date = sell_candidate[0]
            #print(buy_date, sell_date)
            acc_ror *= 1.007
            ax_ror.append(sell_date)
            ay_ror.append(acc_ror)
            # 0.01 - (수수료 0.001 + 슬리피지 0.002)
            count_trading += 1

    #view_chart(df, ax_ror, ay_ror, cond_buy)

    return acc_ror

'''
for ticker in ["KRW-XRP", "KRW-DOGE", "KRW-ETC", "KRW-ETH", "KRW-BTC", "KRW-ADA", "KRW-EOS", "KRW-MARO", "KRW-XLM", "KRW-AQT", "KRW-BCH", "KRW-LTC", "KRW-BTT", "KRW-ARK"]:
    df = get_ohlcv(ticker)
    df.to_excel(f"backtesting/gap_backtesting/result/{ticker}.xlsx")
    print(f'{ticker} 엑셀 데이터 변환 완료..')
'''
for ticker in ["KRW-XRP", "KRW-DOGE", "KRW-ETC", "KRW-ETH", "KRW-BTC", "KRW-ADA", "KRW-EOS", "KRW-MARO", "KRW-XLM", "KRW-AQT", "KRW-BCH", "KRW-LTC", "KRW-BTT", "KRW-ARK"]:
#for ticker in ["KRW-BTC"]:
    df = pd.read_excel(f"backtesting/gap_backtesting/result/{ticker}.xlsx", index_col=0)
    ror = short_trading_for_1percent(df)
    period_profit = df.iloc[-1, 3] / df.iloc[0, 0]
    print(ticker, f"초단타시 수익률: {ror:.2f} 단순 보유시 기간 수익률: {period_profit:.2f} 손절 횟수: {count_stop_loss} 거래 횟수: {count_trading}")
