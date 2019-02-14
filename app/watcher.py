import tornado.websocket
import json
import time
import requests
import threading
from tornado import gen, httpclient
from bs4 import BeautifulSoup

from libs.utils import Timer
from app.notice import Notice

class Watcher:
    
    
    def __init__(self):
        self.target_coins = dict()
        self.notice = Notice()
        
        headers = dict()
        headers['host'] = 'wss.bithumb.com'
        headers['origin'] = 'https://www.bithumb.com'
        headers['Sec-WebSocket-Key'] = 'dTtYGte48lwyP0g/Lv3P2Q=='
        headers['Sec-WebSocket-Version'] = '13'
        
        self.wss_headers = headers
        
        self.xcoin_trade_30M_dict = dict()
      
    def get_total_amouts(self):
    
        soup = BeautifulSoup(requests.get('https://www.bithumb.com/').text,
                             'html.parser')
    
        tr_elm_list = soup.select("#tableAsset > tbody > tr")
    
        for i in tr_elm_list:
            _amounts_text = i.select_one('td:nth-child(5)').get_text()
            _amounts = _amounts_text.replace(' ', '').replace('억', '').replace(
                '조', '')
            if _amounts_text.find('억') == -1 or int(_amounts) < 1000:
                continue
        
            _name = \
            i.select_one('td:nth-child(1) a span').get_text().split('/')[0]
            
            _kr_name = i.select_one('td:nth-child(1) a strong').get_text().strip()
            
            _price = \
            i.select_one('td:nth-child(2) strong').get_text().replace(',','').replace('원','')
            
            
            
            self.target_coins[_name] = dict()
            self.target_coins[_name]['amounts'] =_amounts
            self.target_coins[_name]['price'] = _price
            self.target_coins[_name]['kr_name'] = _kr_name
            
        
    def set_not(self, f):
        f = not f

    def get_tick(self, price):
      
      if type(price) is str:
        _price = int(float(price))
      elif type(price) is int:
        _price = int(price)
      else:
        return 0
  
      tick = 0
  
      if _price > 0:
        digit = len(str(_price))
    
        if digit == 1:
          tick = 0.01
        if digit == 2:
          tick = 0.05
        if digit == 3:
          tick = 1
        if digit == 4:
          tick = 2
        if digit == 5:
          tick = 50
        if digit == 6:
          tick = 100
        if digit == 7:
          tick = 1000
      else:
        digit = len(price)
        if digit == 4:
          tick = 0.01
  
      return tick

    @gen.coroutine
    def transaction(self, currency):
        
        url = httpclient.HTTPRequest("wss://wss.bithumb.com/public",
                                     connect_timeout=5, headers=self.wss_headers)
        client = yield tornado.websocket.websocket_connect(url)
        client.write_message(
            '{"currency":"BTC","tickDuration":"24H","service":"transaction"}')
        
        timer = Timer()
        
        record_score = list()
        shecksheck_price_dict = dict()
        shecksheck_point = 0
        shecksheck_noti = False
        
        pingping_price_list = list()
        tick = self.get_tick(currency)
        while True:
            msg = yield client.read_message()
            print("msg is %s" % msg)
            for i in json.loads(msg)['data']:
                record_score.append(i)
            
            # 쉑쉑이 감지
            if record_score[-1]['type'] != record_score[-2]['type'] and \
                    int(record_score[-1]['units_traded']) - 5 < \
                    record_score[-2]['type'] < int(
                record_score[-1]['units_traded']) + 5:
                shecksheck_point += 1
            else:
                shecksheck_point = 0
            
            # 1분간격으로 쉑쉑이가 언제 나타났는지 확인 처음 나타난 것이리면 노티 쿨타임 30분
            if shecksheck_point == 3:
                if hasattr(shecksheck_price_dict, record_score[-1]['price']):
                    appear_price_list = shecksheck_price_dict[
                        record_score[-1]['price']]
                    _time = time.time() * 1000
                    
                    # 직전 timestamp 보다 2분 이상이상 차이가 나면 추가한다.
                    if appear_price_list[-1] + (60 * 2) < _time:
                        appear_price_list.append(_time)
                
                else:
                    shecksheck_price_dict[record_score[-1]['price']] = list()
                    shecksheck_price_dict[record_score[-1]['price']].append(
                        time.time() * 1000)
                
                # if not shecksheck_noti:
                #     print(record_score[-1]['price'])
                #     shecksheck_noti = not shecksheck_noti
                #     timer.setTimeout(self.set_not, 60 * 30, args=shecksheck_noti)
            
            pingping_price_dict = dict()
            pingping_point = 0
            
            # 핑핑이 감지
            # 길이가 2보다 크거나 같고 price 가 직전과 현재 모두 tick 와 같다면 포인트 증가
            if len(record_score[-2]) >= 2 and record_score[-1]['type'] == \
                    record_score[-2]['type'] and record_score[-2]['price'] == \
                    record_score[-1]['price'] == tick:
                pingping_point += 1
            else:
                pingping_point = 0
            
            if pingping_point > 5:
                if hasattr(pingping_price_dict, record_score[-1]['price']):
                    pingping_appear_price_list = pingping_price_dict[
                        record_score[-1]['price']]
                    _time = time.time() * 1000
                    
                    # 직전 timestamp 보다 2분 이상 차이가 나면 추가한다.
                    if pingping_appear_price_list[-1] + (60 * 2) < _time:
                        pingping_appear_price_list.append(_time)
                
                else:
                    shecksheck_price_dict[record_score[-1]['price']] = list()
                    shecksheck_price_dict[record_score[-1]['price']].append(
                        time.time() * 1000)
                
                    
            if msg is None: break

    def swing(self, currency, minutes=30):
        """
            큼직한 등락을 보기 위한 프로세스
        :param currency:
        :return:
        """
        print('swing {} {} start'.format(minutes, currency))
        
        
        tick = self.get_tick(self.target_coins[currency]['price'])
        if tick == 0:
            print('unknown tick -- method returned')
            return
        
        noti_cool = 0
        
        while True:
            go_noti = False
            xcoin_trade_30M = json.loads(requests.get('https://www.bithumb.com/resources/chart/{}_xcoin_trade_30M.json'.format(currency)).text)[-3:]
            # xcoin_trade_30M[0][0] timestamp
            # xcoin_trade_30M[0][1] 시
            # xcoin_trade_30M[0][2] 종
            # xcoin_trade_30M[0][3] 고
            # xcoin_trade_30M[0][4] 저
            # xcoin_trade_30M[0][5] 거래량
            
            price_gap = float(xcoin_trade_30M[2][2]) - float(xcoin_trade_30M[0][2])
            if (float(xcoin_trade_30M[0][1]) - float(xcoin_trade_30M[1][2])) > tick * 10 and float(xcoin_trade_30M[1][2]) - (tick * 4) > float(xcoin_trade_30M[2][2]):
                signal = '-'
                go_noti = True
            elif float(xcoin_trade_30M[1][2]) - float(xcoin_trade_30M[0][1]) > tick * 10  and float(xcoin_trade_30M[0][2]) < float(xcoin_trade_30M[1][2]) and float(xcoin_trade_30M[1][2]) < float(xcoin_trade_30M[2][2]):
                signal = '+'
                go_noti = True
                
            if go_noti:
                if noti_cool + 60 * 30 < int(time.time()):
                    print('swing {} {}'.format(currency,signal),
                              'gap: {} cp: {}'.format(price_gap,
                                                      xcoin_trade_30M[
                                                          1][2]))
                    self.notice.notice('swing {} {}'.format(self.target_coins[currency]['kr_name'],signal),
                              'gap: {} cp: {}'.format(price_gap,
                                                      xcoin_trade_30M[
                                                          1][2]), level=(1,))
                    noti_cool = int(time.time())
                
            # print(currency, price_gap, xcoin_trade_30M[0][2], xcoin_trade_30M[1][2])
            # 매 정해진 시간 정각에 마춰준다.
            time.sleep( 60 * minutes  - int(time.time()) % minutes)
            
    def get_xcoin_trade(self, minutes=60, loop=True):
        """
            분봉을 가져온다. default 30분봉
            default turm : 1h
        :param currency:
        :return:
        """
        
        print('get_xcoin_trade start')
        
        while loop:
            for idx, val in enumerate(self.target_coins):
                tick = self.get_tick(self.target_coins[val]['price'])
            
                if tick == 0:
                    print('unknown tick -- method returned')
                    continue
                    
                xcoin_trade_30M = json.loads(requests.get(
                    'https://www.bithumb.com/resources/chart/{}_xcoinTrade_30M.json'.format(
                        val)).text)
                
                # 1.5시간 거래량이 일정수준 미달이면 스킵
                amount = 0
                for i in xcoin_trade_30M:
                    amount += float(i[5])
            
                # 최소 천만이상
                if amount * float(self.target_coins[val]['price']) < 10000000:
                    continue
                xcoin_trade_dict = dict()
                xcoin_trade_dict['xcoin_trade'] = xcoin_trade_30M
                xcoin_trade_dict['tick'] = tick
                
                self.xcoin_trade_30M_dict[val] = xcoin_trade_dict
                
            print(self.xcoin_trade_30M_dict)
            time.sleep(60 * minutes)
            # 매 정해진 시간 정각에 마춰준다.
            # 정각을 피하기 위해서 15초 전에 미리 갱신한다.
            # time.sleep( 60 * minutes  - int(time.time()) % minutes - 15)
            
    def big_tick(self, minutes=30, level=1, loop=True):
        """
            현재 제일 틱차이가 많이 나는 코인을 알려준다.
            default turm : 30m
        :param currency:
        :return:
        """
        
        print('start big_tick')
        
        while loop:
            high_list = list()
            row_list = list()
            if len(self.xcoin_trade_30M_dict) > 0:
                for idx, val in enumerate(self.xcoin_trade_30M_dict):
                    
                    xcoin_trade_30M = self.xcoin_trade_30M_dict[val]['xcoin_trade'][-3:]
                    tick = self.xcoin_trade_30M_dict[val]['tick']
                    # xcoin_trade_30M[0][0] timestamp
                    # xcoin_trade_30M[0][1] 시
                    # xcoin_trade_30M[0][2] 종
                    # xcoin_trade_30M[0][3] 고
                    # xcoin_trade_30M[0][4] 저
                    # xcoin_trade_30M[0][5] 거래량
                    
                    price_gap = int(
                        (float(xcoin_trade_30M[2][2]) - float(xcoin_trade_30M[0][1])) / tick)
                    
                    # 갭이 + 이고 high 가 처음이거나 이전 gap 보다 크면
                    if price_gap >= 0:
                        _high = list()
                        _high.append(str(price_gap))
                        _high.append(str(xcoin_trade_30M[2][2]))
                        _high.append(self.target_coins[val]['kr_name'])
                    
                        high_list.append(_high)
                    
                    elif price_gap < 0:
                        _row = list()
                        _row.append(str(price_gap))
                        _row.append(str(xcoin_trade_30M[2][2]))
                        _row.append(self.target_coins[val]['kr_name'])
                    
                        row_list.append(_row)
                
                high_list = sorted(high_list, key=lambda k: float(k[0]), reverse=True)
                row_list = sorted(row_list, key=lambda k: float(k[0]))
                
                high_list = '| '.join([' '.join(i) for i in high_list])
                row_list = '| '.join([' '.join(i) for i in row_list])
                
                self.notice.notice('big tick +', high_list, level=level)
                self.notice.notice('big tick -', row_list, level=level)
            
                # 매 정해진 시간 정각에 마춰준다.
                time.sleep(60 * minutes - int(time.time()) % minutes)
                
            else:
                time.sleep(15)
        
    
    def red_line(self, minutes=30, level=1, loop=True):
        """
            상승세가 가장 강한 코인을 알려준다.
            default turm : 30m
        :param currency:
        :return:
        """
        
        print('red_line start')
        
        while loop:
            if len(self.xcoin_trade_30M_dict) > 0:
                results = list()
                for idx, val in enumerate(self.xcoin_trade_30M_dict):
                    coins = list()
                    xcoin_trade_30M = self.xcoin_trade_30M_dict[val]['xcoin_trade']
                
                    red_line_count = len([i for i in xcoin_trade_30M[-10:] if
                            float(i[1]) < float(i[2])])
                    if red_line_count == 0:
                        continue
                    
                    coins.append(str(red_line_count))
                    coins.append(self.target_coins[val]['kr_name'])
                    results.append(coins)
                    
                results = sorted(results, key=lambda k: float(k[0]), reverse=True)
                results = '| '.join(['-'.join(i) for i in results])
                
                if len(results) == 0:
                    results = '없음'
                    
                self.notice.notice('red line',results, level=level)

                # 매 정해진 시간 정각에 마춰준다.
                time.sleep(60 * minutes - int(time.time()) % minutes)
                
            else:
                time.sleep(15)
        
    def feeler(self, minutes=60, level=1, loop=True):
        """
            더듬이가 있는 녀석, 급등을 시도했다가 실패한 녀석을 알려준다.
            default turm : 60m
        :param currency:
        :return:
        """
        
        print('feeler start')
        
        while loop:
            if len(self.xcoin_trade_30M_dict) > 0:
                results = list()
                for idx, val in enumerate(self.xcoin_trade_30M_dict):
                    coins = list()
                    
                    xcoin_trade_30M = self.xcoin_trade_30M_dict[val]['xcoin_trade']
                    # 고가가 종가보다 15틱이상인 녀석이 있는 지 확인
                    feelder_count = len([i for i in xcoin_trade_30M[-10:] if
                            float(i[1]) < float(i[2]) and float(i[2]) + float(
                                (self.xcoin_trade_30M_dict[val]['tick'] * 15)) < float(
                                i[3])])
                                
                    if feelder_count == 0:
                        continue
                    
                    coins.append(str(feelder_count))
                    coins.append(self.target_coins[val]['kr_name'])
                    results.append(coins)
                
                results = sorted(results, key=lambda k: float(k[0]), reverse=True)
                results = '| '.join(['-'.join(i) for i in results])
                
                if len(results) != 0:
                    self.notice.notice('feeler', results, level=level)

                # 매 정해진 시간 정각에 마춰준다.
                time.sleep(60 * minutes - int(time.time()) % minutes)
                
            else:
                time.sleep(15)

    def get_high(self, minutes=0.5, level=1):
        """
            4분안에 8틱이 상승한 녀석알림
            default turm : 1m
        :return:
        """
        
        print('start get_high')
        
        while True:
            for idx, val in enumerate(self.target_coins):
                tick = self.get_tick(self.target_coins[val]['price'])
            
                if tick == 0:
                    print('unknown tick -- method returned')
                    continue
            
                print(val)
                try:
                    xcoin_trade_01M = json.loads(requests.get(
                        'https://www.bithumb.com/resources/chart/{}_xcoinTrade_01M.json'.format(
                            val)).text)
                except Exception as e :
                    print(e)
                    pass
                
                _list = [i for i in xcoin_trade_01M[-2:] if
                    float(i[1]) < float(i[2])]

                if 2 == len(_list):
                    print(xcoin_trade_01M[-2:])
                    print(_list)
                
                if 2 == len(_list) and _list[1][2] - _list[0][1] > (tick * 5):
                    self.notice.notice('get_high', val, level=level)
                    
            # 매 정해진 시간 정각에 마춰준다.
            time.sleep(60 * minutes - int(time.time()) % minutes)
                
    def start(self):
        self.get_total_amouts()
        print(self.target_coins)
        # threading.Thread(target=self.swing, args=('TRX',1)).start()
        # for idx, val in enumerate(self.target_coins):
        #     threading.Thread(target=self.swing, args=(val,1)).start()
        # self.get_xcoin_trade(sec=10, loop=False)
        # self.big_tick(sec=10, loop=False)
        # self.red_line(sec=10, loop=False)
        # self.feeler(sec=10, loop=False)
        
        
        
        
        # --
        # threading.Thread(target=self.get_high).start()
        # threading.Thread(target=self.get_xcoin_trade).start()
        # threading.Thread(target=self.big_tick).start()
        # threading.Thread(target=self.red_line).start()
        # threading.Thread(target=self.feeler).start()
        # --
        
        # --
        # self.get_xcoin_trade(loop=False)
        # self.big_tick(loop=False)
        threading.Thread(target=self.get_high).start()
        # --
        
    # def flowing_BTC(self):
    
    
    def flowing_BTC(self):
        pass
    
    def focus(self):
        pass
    
    def loos_cut(self):
        pass
    
if __name__ == "__main__":
    watcher = Watcher()
    watcher.start()

# 1시간 안에 10틷 이상 한 방향으로 움직였다. 알림
# 쉑쉑이는 가격을 무너트린 다음에 들어간다.
# 코인별 큰단위 갯수는 10틱
# 거래량이 요동치면 알림? (실시간으로 업데이트)
# 틱이 요동치면 알림? (30분에 1번씩 업데이트)
# 거래량이 1천이상이고 (한시간에 한번씩 업데이트)

# 비트코인이 상승세이고 그것을 따라가는 코인을 찾는다.
# 비트코인이
# 더듬이가 있는 코인, 급상승을 겪은 코인 = 세력코인
#

