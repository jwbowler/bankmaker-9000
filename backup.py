import time
import json
import socket



class Book:
    def update(book_dict):
        self.symbol = book_dict['symbol']
        self.buy = book_dict['buy']
        self.sell = book_dict['sell']


class Trade:
    def __init__(self, trade_dict):
        self.symbol = trade_dict.symbol
        self.price = trade_dict.price
        self.size = trade_dict.size


class Stock:

    ##has: current book, list of transactions, list of historical best bids and best asks
    def __init__(self, symbol):
        self.symbol = symbol
        self.book = Book() # current book
        self.trades = []
        
        # lists of (price, size) tuples
        self.best_bids = []
        self.best_asks = []
        
        self.market_val = []    # current_val
        self.market_avg1 = []   # average_val
        
    # type = book, trade, fill
    def update(self, update_dict):
        if update_dict['type'] == 'book':
            self.book.update(update_dict)
            
            if len(update_dict['buy']) > 0:
                assert len(update_dict['buy'][0]) == 2
                new_best_bid = (time.time(), update_dict['buy'][0])
                self.best_bids.append(update_dict['buy'][0])
                self.updateMarketValue()
            
            if len(update_dict['sell']) > 0:
                assert len(update_dict['sell'][0]) == 2
                new_best_ask = (time.time(), update_dict['sell'][0])
                self.best_asks.append(update_dict['sell'][0])
                self.updateMarketValue()
            
        elif update_dict['type'] == 'trade':
            self.trades.append(Trade(update_dict))
         
        elif update_dict['type'] == 'fill':
            pass
            
        else:
            assert False
            
            
    def calc_liquidated_value(self, shares):
        value = 0
        if shares > 0:
            for (price, size) in book.buy:
                if size < shares:
                    value += price * size
                    shares -= size
                else:
                    value += price * shares
                    break
        else:
            for (price, size) in book.sell:
                if size < shares:
                    value -= price * size
                    shares -= size
                else:
                    value -= price * shares
                    break
        return value
        
    def getMarketValue(self):
        # naive
        best_bids = self.best_bids[-1][0]
        best_asks = self.best_asks[-1][0]
        marketValue = 0.5*(best_bids+best_asks)
        
        return marketValue
        
    def updateMarketValue(self):
        numPrev = min(len(self.market_val), 99)
        current = self.getMarketValue()
        average = 1.0*(numPrev*self.market_avg1[-1] + current)/(numPrev+1)
        
        self.market_val.append(current)
        self.market_avg1.append(average)



class Market:

    def __init__(self, symbols):
        stocks = {symbol: Stock(symbol) for symbol in SYMBOLS}
        is_open = False

    def update(self, book_message):
        symbol = book_message['symbol']
        stocks[symbol].update(book_message)



class Portfolio:

    def __init__(self):
	    self.received_hello = False
        self.numrequests = 0
        self.pending_orders = {}

    def recv_hello(hello_message):
        self.balance = 0
        self.positions = {symbol: 0 for symbol in SYMBOLS}
        self.received_hello = True

    def handle_ack(ack_message):
        id = ack_message['order_id']
        self.pending_orders[id].handle_ack(ack_message)



    def buy(self, symbol, price, size):
        request = jsonify({\
            "type": "add", \
            "order_id": self.numrequests, \
            "symbol": symbol, \
            "dir": "BUY", \
            "price": price, \
            "size": size})
        self.numrequests += 1
        s.send(request)
        print request
	res = json.loads(s.recv())
        print s.buf
	return res
            
        
    def sell(self, symbol, price, size):
        request = jsonify({\
            "type": "add", \
            "order_id": self.numrequests, \
            "symbol": symbol, \
            "dir": "SELL", \
            "price": price, \
            "size": size})
        self.numrequests += 1
        s.send(request)
        return json.loads(s.recv())
    
    def convert(self, dir, size):
        request = jsonify({\
            "type": "convert", \
            "order_id": self.numrequests, \
            "symbol": "CORGE", \
            "dir": dir, \
            "size": size})
        self.numrequests += 1
        s.send(request)
        return json.loads(s.recv())
        
      # fixed cost of 100 per conversion (regardless of size)
      # one CORGE = 0.3 FOO + 0.8 BAR
      # returns ACK or REJECT

    def cancel(self, order_id):
        request = jsonify({\
            "type": "cancel", \
            "order_id": order_id})
        s.send(request)
        json.loads(s.recv())
      # returns OUT even if order_id is invalid


class Strategy:
    def __init__(self, market, portfolio):
        self.market = market
        self.portfolio = portfolio

    def step(self):
        # Works with CORGE only for now
        cost = 100
        corge = self.market.stocks['CORGE']
        foo = self.market.stocks['FOO']
        bar = self.market.stocks['BAR']

        corgeAsk = corge.best_asks[-1]
        corgeBid = corge.best_bids[-1]
        fooAsk = foo.best_asks[-1]
        fooBid = foo.best_bids[-1]
        barAsk = bar.best_asks[-1]
        barBid = bar.best_bids[-1]
        
        print 
        print 
        if corgeBid[0]-(0.3*fooAsk[0]+0.8*barAsk[0])>cost:
            num = min(fooAsk[1]/0.3, barAsk[1]/0.8, corgeBid[1])
            self.portfolio.buy('CORGE', corgeBid[0], num)
            self.portfolio.convert('SELL', num)
            self.portfolio.sell('FOO', fooAsk[0], num*0.3)
            self.portfolio.sell('BAR', barAsk[0], num*0.8)
        elif corgeAsk[0]-(0.3*fooBid[0]+0.8*barBid[0])>cost:
            num = min(fooBid[1]/0.3, barBid[1]/0.8, corgeAsk[1])
            self.portfolio.sell('CORGE', corgeAsk[0], num)
            self.portfolio.convert('BUY', num)
            self.portfolio.buy('FOO', fooBid[0], num*0.3)
            self.portfolio.buy('BAR', barBid[0], num*0.8)
        


class Order:
    def __init__(self, id, symbol, dir, price, size):
        self.id = id
        self.symbol = symbol
        self.dir = dir
        self.price = price
        self.size = size

        # possible states: CREATED, ACKED, CANCELLING
        self.state = 'CREATED'

    def handle_ack(self):
        pass



def calc_pnl(portfolio, stocks):
    return portfolio.balance + sum([stock.get_liquidated_value() for stock in stocks])




class mysocket:

    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock
        self.buf = ""

    def connect(self, host, port):
        self.sock.connect((host, port))

    def send(self, msg):
        self.sock.send(msg)

    def recv(self):
        data = ''
        message = ''
        while True:
          data += self.sock.recv(BUFFER_SIZE)
          if not data:
            break
          self.buf += data
          if '\n' not in self.buf:
            message += self.buf
            self.buf = ''
          else:
            message, self.buf = self.buf.split('\n', 1)
            return message
        

def jsonify(p):
    return json.dumps(p) + '\n'


def send_hello(): #MUST ISSUE FIRST!!

    request = jsonify({\
                       "type": "hello", \
                       "team": TEAM_NAME })
    s.send(request)
    print "Sent request"
    res = json.loads(s.recv())
    print "Response:", res
    return res


if __name__ == '__main__':

    TEST = True
    TEST_INDEX = 2 # 0 = slow, 1 = normal, 2 = empty market
    if TEST:
        TCP_IP = '10.0.207.145'
    else:
        TCP_IP = 'real exchange ip'
    TCP_PORT = 25000 + TEST_INDEX
    BUFFER_SIZE = 4096
    s = mysocket()
    s.connect(TCP_IP, TCP_PORT)
    
    # s.close() at some point

    SYMBOLS = ['FOO', 'BAR', 'BAZ', 'QUUX', 'CORGE']
    TEAM_NAME = 'BANKMAKERS'

    stocks = [Stock(symbol) for symbol in SYMBOLS]
    portfolio = Portfolio()

    market = Market(SYMBOLS)
    portfolio = Portfolio()
    strategy = Strategy(market, portfolio)

    def handle(message):
        t = message['type']

        if t == 'hello':
            portfolio.recv_hello(message)

        if t == 'market_open':
            market.is_open = message['open']

        if t == 'error':
            assert False

        if t == 'book':
            market.update(message)

        if t == 'trade':
            market.update(message)

        if t == 'ack':
            portfolio.handle_ack(message)

        if t == 'reject':
            portfolio.handle_reject(message)

        if t == 'fill':
            portfolio.handle_fill(message)

        if t == 'out':
            portfolio.handle_out(message)


#    while True:
        # block until received message, and un-JSONify it
        # handle(message)
        # strategy.step()
#	pass

    #listen for book updates...
    # if "type" == "book", put this JSON object in a "book" variable (analogous for "trade" type)
    send_hello()
    portfolio.buy("FOO", 100, 1)
