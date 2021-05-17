import threading
import queue
import time
import pyupbit
import datetime
from collections import deque
TICKER = "KRW-ADA"
CASH = 80000

class Consumer(threading.Thread):
    def __init__(self, q):
        super().__init__()
        self.q = q
        self.ticker = TICKER

        self.ma5 = deque(maxlen=5)
        self.ma10 = deque(maxlen=10)
        self.ma15 = deque(maxlen=15)
        self.ma50 = deque(maxlen=50)
        self.ma120 = deque(maxlen=120)

        df = pyupbit.get_ohlcv(self.ticker, interval="minute1")
        self.ma5.extend(df['close'])
        self.ma10.extend(df['close'])
        self.ma15.extend(df['close'])
        self.ma50.extend(df['close'])
        self.ma120.extend(df['close'])


    def run(self):
        price_curr = None  # 현재 가격
        hold_flag = False  # 보유 여부
        wait_flag = False  # 대기 여부

        with open("key/upbit_key.txt", "r") as f:
            access = f.readline().strip()
            secret = f.readline().strip()

        upbit = pyupbit.Upbit(access, secret)
        #cash  = upbit.get_balance()  # 2개 이상 종목 돌릴 시 모든 cash 코드 임의 설정
        cash = CASH
        print("보유현금:", cash)

        i = 0

        while True:
            try:
                if not self.q.empty():
                    if price_curr != None:
                        self.ma5.append(price_curr)
                        self.ma10.append(price_curr)
                        self.ma15.append(price_curr)
                        self.ma50.append(price_curr)
                        self.ma120.append(price_curr)

                    curr_ma5 = sum(self.ma5) / len(self.ma5)
                    curr_ma10 = sum(self.ma10) / len(self.ma10)
                    curr_ma15 = sum(self.ma15) / len(self.ma15)
                    curr_ma50 = sum(self.ma50) / len(self.ma50)
                    curr_ma120 = sum(self.ma120) / len(self.ma120)

                    price_open = self.q.get()
                    if hold_flag == False:
                        price_buy  = price_open * 1.005
                        price_sell = price_open * 1.015
                    wait_flag  = False

                price_curr = pyupbit.get_current_price(self.ticker)
                if price_curr == None:
                    continue

                if hold_flag == False and wait_flag == False and \
                    price_curr >= price_buy and curr_ma5 >= curr_ma10 and \
                    curr_ma10 >= curr_ma15 and curr_ma15 >= curr_ma50 and \
                    curr_ma50 >= curr_ma120 and curr_ma15 <= curr_ma50 * 1.03:
                    # 0.05%
                    while True:
                        ret = upbit.buy_market_order(self.ticker, cash * 0.9995)
                        if ret == None or "error" in ret:
                            print("<< 매수 주문 Error >>")
                            time.sleep(0.5)
                            continue
                        print("매수 주문", ret)
                        break

                    while True:
                        order = upbit.get_order(ret['uuid'])
                        if order != None and len(order['trades']) > 0:
                            print("<< 매수 주문이 체결되었습니다 >>\n", order)
                            break
                        else:
                            print("매수 주문 대기 중...")
                            time.sleep(0.5)

                    while True:
                        volume = upbit.get_balance(self.ticker)
                        if volume != None and volume != 0:
                            break
                        print("보유량 계산중...")
                        time.sleep(0.5)

                    while True:
                        price_sell = pyupbit.get_tick_size(price_sell)
                        ret = upbit.sell_limit_order(self.ticker, price_sell, volume)
                        if ret == None or 'error' in ret:
                            print("<< 지정가 매도 주문 Error >>")
                            time.sleep(0.5)
                        else:
                            print("<< 지정가 매도주문이 접수되었습니다 >>\n", ret)
                            hold_flag = True
                            break
                    
                    #cash = upbit.get_balance()
                    cash -= (price_buy * volume)

                if hold_flag == True:
                    uncomp = upbit.get_order(self.ticker)

                    if (price_curr / price_buy) <= 0.95:  # 5% 하락시 손절 매도
                        while True:
                            upbit.cancel_order(uncomp[0]['uuid'])
                            if len(upbit.get_order(self.ticker)) == 0:
                                print("<< 지정가 매도주문이 취소되었습니다 >>\n", ret)
                                break

                        upbit.sell_market_order(self.ticker, volume)
                        while True:
                            volume = upbit.get_balance(self.ticker)
                            if volume == 0:
                                print("<< 손절 주문(-5%)이 완료되었습니다 >>")
                                cash += CASH * 0.95
                                hold_flag = False
                                wait_flag = True
                                break
                            else:
                                print("손절 주문(-5%) 대기중...")
                                time.sleep(0.5)
                    elif uncomp != None and len(uncomp) == 0:
                        #cash = upbit.get_balance()
                        cash += CASH * 1.01
                        if cash == None:
                            continue
                        print("<< 지정가 매도가 체결되었습니다 >>")
                        hold_flag = False
                        wait_flag = True

                # 10 seconds
                if i == (5 * 10):
                    print(f"[{datetime.datetime.now()}]")
                    print(f"{TICKER} 보유량:{upbit.get_balance_t(self.ticker)}, 보유KRW: {cash},  hold_flag= {hold_flag}, wait_flag= {wait_flag} signal = {curr_ma5 >= curr_ma10 and curr_ma10 >= curr_ma15 and curr_ma15 >= curr_ma50 and curr_ma50 >= curr_ma120 and curr_ma15 <= curr_ma50 * 1.03}")
                    print(f"현재: {price_curr}, 매수 목표: {int(price_buy)}, 지정 매도: {price_sell}, 손절 예상: {int(price_buy * 0.9)}")
                    i = 0
                i += 1
            except:
                print("error")

            time.sleep(0.2)

class Producer(threading.Thread):
    def __init__(self, q):
        super().__init__()
        self.q = q

    def run(self):
        while True:
            price = pyupbit.get_current_price(TICKER)
            self.q.put(price)
            time.sleep(60)

now = datetime.datetime.now()
print(f'환영합니다 -- Upbit Auto Trading -- [{now.year}-{now.month}-{now.day} {now.hour}:{now.minute}:{now.second}]')
print('트레이딩 대기중...')
while True:
    now = datetime.datetime.now()
    if now.second == 1:  # 대기 후 1초에 시작
        q = queue.Queue()
        Producer(q).start()
        Consumer(q).start()
        break
