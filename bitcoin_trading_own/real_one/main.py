import datetime
import time
import pandas as pd
from Strategy.MACD import macd
import pyupbit
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# 환경 변수나 설정 파일에서 민감한 정보 불러오기
slack_token = ""
channel = ""

client = WebClient(token=slack_token)

access_key = ""
secret_key = ""

# Upbit 객체 생성
upbit = pyupbit.Upbit(access_key, secret_key)

def calculate_current_asset():
    current_krw_balance = upbit.get_balance("KRW")
    owned_coins_info = upbit.get_balances()

    # Calculate the current coin assets
    total_coin_assets = 0
    for coin in owned_coins_info:
        if coin['currency'] != 'KRW':
            coin_quantity = float(coin['balance'])
            coin_price = pyupbit.get_current_price(f"KRW-{coin['currency']}")
            total_coin_assets += coin_quantity * coin_price

    # Calculate the current total assets
    current_total_assets = current_krw_balance + total_coin_assets
    return current_total_assets


def get_next_wait_time(interval: str) -> int:
    now = datetime.datetime.now()
    minutes = int(interval.replace('minute', ''))  # 'minute15'에서 숫자만 추출하여 분 단위로 변환
    next_time = now + datetime.timedelta(minutes=minutes - now.minute % minutes, seconds=-now.second, microseconds=-now.microsecond)
    wait_time = (next_time - now).total_seconds()
    return wait_time


def save_daily_report(trade_history: pd.DataFrame) -> None:
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    file_name = f'trade_history_{date_str}.csv'
    trade_history.to_csv(file_name, index=False)
    print(f'Saved daily report to {file_name}')

def main(coin: str, interval: str = "minute15") -> pd.DataFrame:
    trade_history = pd.DataFrame(columns=['timestamp', 'action', 'price', 'amount', 'value', 'holding_profit', 'trade_profit'])
    now = datetime.datetime.now()

    try:
        df = pyupbit.get_ohlcv(coin, interval=interval)
        current_price = df['close'].iloc[-1]
        signal = macd(df)

        # 거래 수행 및 내역 기록
        if signal == 'buy':
            krw_balance = upbit.get_balance("KRW")
            fee = 0.0005
            krw_balance = krw_balance / (1 + fee)
            buy_result = upbit.buy_market_order(coin, krw_balance)
            trade_history = trade_history.append({
                'timestamp': now, 
                'action': 'buy', 
                'price': current_price, 
                'amount': buy_result['volume'], 
                'value': buy_result['price']
            }, ignore_index=True)
            client.chat_postMessage(channel=channel, text='매수 했습니다.')

        elif signal == 'sell':
            coin_balance = upbit.get_balance(coin.split('-')[1])
            fee = 0.0005
            coin_balance = coin_balance / (1 + fee)
            sell_result = upbit.sell_market_order(coin, coin_balance)
            trade_history = trade_history.append({
                'timestamp': now, 
                'action': 'sell', 
                'price': current_price, 
                'amount': sell_result['volume'], 
                'value': sell_result['price']
            }, ignore_index=True)
            client.chat_postMessage(channel=channel, text='매도 했습니다.')
        else:
            client.chat_postMessage(channel=channel, text='nothing just' + signal)

    except Exception as e:
        print(f"Error occurred: {e}")
        client.chat_postMessage(channel=channel, text=f'오류 발생: {e}')

    return trade_history

if __name__ == "__main__":
    coin = "KRW-SUI"
    interval = "minute15"
    client.chat_postMessage(channel=channel, text='프로그램이 시작되었습니다')
    trade_history = pd.DataFrame(columns=['timestamp', 'action', 'price', 'amount', 'value', 'holding_profit', 'trade_profit'])
    last_day = datetime.datetime.now().day
    initial_asset = calculate_current_asset()
    initial_coin_price = pyupbit.get_current_price(coin)
    
    while True:
        # 다음 실행 시간까지 대기
        wait_time = get_next_wait_time(interval)
        print(f"Waiting {wait_time} seconds until the next time interval.")
        time.sleep(wait_time)

        # 설정한 간격에 맞춰 매매 실행
        trade_history = main(coin, interval)
        asset = calculate_current_asset()
        coin_price = pyupbit.get_current_price(coin)
        ratio = asset / initial_asset
        coin_ratio = coin_price / initial_coin_price
        print(f"Executed trade at: {datetime.datetime.now()}")
        client.chat_postMessage(channel=channel, text='straegy ratio is ' + str(ratio))
        client.chat_postMessage(channel=channel, text='coin ratio is ' + str(coin_ratio))
        print(f"Current asset: {asset}")

        

        # 하루가 끝날 때마다 거래 내역을 CSV 파일로 저장
        current_day = datetime.datetime.now().day
        if current_day != last_day:
            save_daily_report(trade_history)
            trade_history = pd.DataFrame(columns=['timestamp', 'action', 'price', 'amount', 'value', 'holding_profit', 'trade_profit'])  # 새로운 날을 위한 데이터프레임 초기화
            last_day = current_day