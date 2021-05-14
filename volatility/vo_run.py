import pyupbit
import time
import datetime
TICKER = 'KRW-QTUM'
INTERVAL = 'minute30'
if INTERVAL == 'minute1':
    CANDLE = 1  # INTERVAL과 맞춤 (봉 시간 설정, minute 기준)
    CANDLE_REMAIN = 0  # 분봉마다 타겟 갱신시 거래중지 minute 설정 (line 75)
elif INTERVAL == 'minute3':
    CANDLE = 3
    CANDLE_REMAIN = 2
elif INTERVAL == 'minute5':
    CANDLE = 5
    CANDLE_REMAIN = 4
elif INTERVAL == 'minute10':
    CANDLE = 10
    CANDLE_REMAIN = 9
elif INTERVAL == 'minute15':
    CANDLE = 15
    CANDLE_REMAIN = 14
elif INTERVAL == 'minute30':
    CANDLE = 30
    CANDLE_REMAIN = 29
elif INTERVAL == 'minute60':
    CANDLE = 60
    CANDLE_REMAIN = 59
else:
    print("CANDLE_REMAIN 설정 오류")
    exit()
KVALUE = 0.5  # k값 by 백테스팅
BREAK_POINT = 0.95  # 하락 브레이크포인트 설정 (0.01 == 1%)


def cal_target(ticker):  # 타겟 금액 리턴
    df = pyupbit.get_ohlcv(ticker, INTERVAL)  # 봉 산출
    ago = df.iloc[-2]  # 1봉 전
    current = df.iloc[-1]  # 현재 봉
    range = ago['high'] - ago['low']  # 변동폭 산출
    target = current['open'] + range * KVALUE  # target calculate
    return target

def cal_open_price(ticker):  # 시가 리턴
    df = pyupbit.get_ohlcv(ticker, INTERVAL)  # 봉 호출
    current = df.iloc[-1]  # 현재 봉
    open_price = current['open']  # 시가 산출
    return open_price

def get_ma5(ticker):  # INTERVAL 기준 5봉 이동 평균선 조회
    df = pyupbit.get_ohlcv(ticker, INTERVAL)
    ma = df['close'].rolling(5).mean()
    return ma[-2]

def print_balance(upbit):  # 보유 잔고 출력
    balances = upbit.get_balances()  # 보유 잔고 산출
    print('\n<<< 보유 잔고 현황 >>>')
    for balance in balances:
        print(balance['currency'], ':', balance['balance'])
    print('현재 시간:', datetime.datetime.now())
    print('\n')

def up_down(price, price_open):  # 상승장 하락장 리턴
    return '상승장' if price > price_open else '하락장'


# Login to Upbit
def login():  # 로그인
    f = open('key/upbit_key.txt', 'r')
    lines = f.readlines()
    access = lines[0].strip()  # access key
    secret = lines[1].strip()  # secret key
    f.close()

    try:
        upbit = pyupbit.Upbit(access, secret)  # class instance object
        print('[명선호] 님 환영합니다. -- Upbit Auto Trading --', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    except:
        print('Upbit 로그인 실패')
        exit()

    print_balance(upbit)  # 로그인 당시 전체 잔고 출력

    return upbit


upbit = login()  # 로그인

# 초기화
target = cal_target(TICKER)
price = pyupbit.get_current_price(TICKER)  # 프로그램 시작시 종목 현재가 산출
hold_check = upbit.get_balance(TICKER)
price_open = cal_open_price(TICKER)  # 시가 저장
ticker_balance = upbit.get_balance(TICKER)  # 종목 보유량 저장
ma5 = get_ma5(TICKER)
i = 0

if price <= target:  # 프로그램 시작시 매수진행 check (동작 상태 OK check)
    op_mode = True
else:
    op_mode = False

if hold_check == 0 and hold_check != None:  # 프로그램 시작시 종목보유 check (종목 보유기간동안 재시작 대처)
    hold = False  # 현재 코인 보유 여부
else:
    hold = True

# 프로그램 시작 당시 시드머니 저장 (다중 실행시 시드머니 기준의 n배 매수 필요)
seed_money = upbit.get_balance('KRW')

while True:
    try:
        now = datetime.datetime.now()
        price = pyupbit.get_current_price(TICKER)  # 매 초 현재가 호출
        ticker_balance = upbit.get_balance(TICKER)  # 보유 코인 잔고 저장

        # 매도 - 봉의 종가지점에서 전량매도
        if (now.minute % CANDLE == CANDLE_REMAIN) and (50 <= now.second <= 59):
            if op_mode is True and hold is True:
                upbit.sell_market_order(TICKER, ticker_balance)  # 보유 코인 전량 시장가 매도
                print('매도가 체결되었습니다.')
                hold = False  # 보유여부 False 변경
            op_mode = False  # 타겟 갱신시까지 거래 잠시 중지

        # 봉 넘긴 후(op_mode = False) 5초 텀

        # hh:mm:05 목표가 갱신
        # 매 봉의 5초~10초 타겟, 시가, 동작상태 ON, 이평선 계산, 보유잔고 출력
        if (now.minute % CANDLE == 0) and (5 <= now.second <= 10):
            target = cal_target(TICKER)
            price_open = cal_open_price(TICKER)
            op_mode = True
            ma5 = get_ma5(TICKER)
            print_balance(upbit)

        # 매 초마다 조건 확인후 매수 시도
        if op_mode is True and hold is False and price is not None and price >= target and price_open > ma5:
            # 매수
            krw_balance = upbit.get_balance('KRW')  # 보유 원화 저장
            upbit.buy_market_order(TICKER, krw_balance * 0.24)  # 보유 원화(시드머니)의 n배만큼 시장가 매수 (24%)
            print('매수가 체결되었습니다.')
            hold = True  # 보유여부 True 변경

        # 5% 하락시 강제 매도 후 일시중지
        if op_mode is True and hold is True and price is not None and ((price/target) < BREAK_POINT):
            upbit.sell_market_order(TICKER, ticker_balance)  # 보유 코인 전량 시장가 매도
            print('손절(-5%) 체결되었습니다.')
            hold = False  # 보유여부 False 변경
            op_mode = False  # 일시중지
            time.sleep(5)
    except:
        print('에러 발생!!')

    # 상태 출력
    if i == 10:
        print(f"{now.hour}:{now.minute}:{now.second} << {TICKER} >>")
        print(f"목표가: {target} 현재가: {price} 진입 시그널: {price_open > ma5} 보유상태: {hold} 동작상태: {op_mode}")
        print(f"수익률 KRW: {upbit.get_balance('KRW') - seed_money} 종목 보유량: {ticker_balance} 목표가 돌파: {price >= target} 시가: {price_open} 장 현황:{up_down(price, price_open)}")
        i = 0
    i += 1
    time.sleep(1)
