import errno
import sys
import os
import fcntl
import time
import json
import socket
from threading import Thread


class Book(object):
    def update(self, book_dict):
        self.symbol = book_dict['symbol']
        self.buy = book_dict['buy']
        self.sell = book_dict['sell']


class Trade(object):
    def __init__(self, trade_dict):
        self.symbol = trade_dict['symbol']
        self.price = trade_dict['price']
        self.size = trade_dict['size']


class Stock(object):

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
	if len(self.best_bids) == 0 or len(self.best_asks) == 0:
		return None
        best_bids = self.best_bids[-1][0]
	best_asks = self.best_asks[-1][0]
        marketValue = 0.5*(best_bids+best_asks)

        return marketValue

    def updateMarketValue(self):
        numPrev = min(len(self.market_val), 99)
        current = self.getMarketValue()
	if len(self.market_avg1) == 0:
		return None
        average = 1.0*(numPrev*self.market_avg1[-1] + current)/(numPrev+1)

        self.market_val.append(current)
        self.market_avg1.append(average)



class Market(object):

    def __init__(self, symbols):
        self.stocks = {symbol: Stock(symbol) for symbol in symbols}
        self.is_open = False

    def update(self, book_message):
        symbol = book_message['symbol']
        self.stocks[symbol].update(book_message)



class Portfolio(object):

    def __init__(self):
        self.received_hello = False
        self.counter = 0
        self.pending_orders = {}

    def __str__(self):
        out = "BALANCE = " + str(self.balance)
        for symbol in SYMBOLS:
            out += symbol + ' = ' + str(self.positions[symbol]) + ', '
        return out

    def __repr__(self):
        return self.__str__()

    def recv_hello(self, hello_message):
        self.balance = hello_message['cash']
        syms = hello_message['symbols']
        self.positions = {sym['symbol']: sym['position'] for sym in syms}
        self.received_hello = True

    def handle_ack(self, message):
        order_id = message['order_id']
        order = self.pending_orders[order_id]
        order.handle_ack()

        # sorry...
        if isinstance(order, ConvertOrder):
            self.balance -= 100
            if order.direction == 'BUY':
                self.positions['CORGE'] += order.size
                self.positions['FOO'] -= order.size * 3/10
                self.positions['BAR'] -= order.size * 8/10
            elif order.direction == 'SELL':
                self.positions['CORGE'] -= order.size
                self.positions['FOO'] += order.size * 3/10
                self.positions['BAR'] += order.size * 8/10
            else:
                assert False

        elif isinstance(order, TradeOrder):
            pass
        else:
            assert False


    def handle_reject(self, message):
        order_id = message['order_id']
        del self.pending_orders[order_id]

    def handle_fill(self, message):
        order_id = message['order_id']

        if message['dir'] == 'BUY':
            self.balance -= message['price'] * message['size']
            self.positions[message['symbol']] += message['price'] * message['size']
        if message['dir'] == 'SELL':
            self.balance += message['price'] * message['size']
            self.positions[message['symbol']] -= message['price'] * message['size']

    def handle_out(self, message):
        order_id = message['order_id']
        del self.pending_orders[order_id]

    def trade(self, symbol, price, size, direction):
        order_id = self.counter
        order = TradeOrder(order_id, symbol, direction, price, size)
        self.pending_orders[order_id] = order

        request = order.get_json_request()
        self.counter += 1
        s.send(request)
        #res = json.loads(s.recv())
        #print s.buf
        #return res
        return order_id

    def buy(self, symbol, price, size):
        self.trade(symbol, price, size, 'BUY')

    def sell(self, symbol, price, size):
        self.trade(symbol, price, size, 'SELL')

        #return json.loads(s.recv())

    def convert(self, direction, size):
        assert size % 10 == 0

        order_id = self.counter
        order = ConvertOrder(order_id, direction, size)
        self.pending_orders[order_id] = order

        request = order.get_json_request()
        self.counter += 1
        s.send(request)
        #return json.loads(s.recv())
        return order_id

      # fixed cost of 100 per conversion (regardless of size)
      # one CORGE = 0.3 FOO + 0.8 BAR
      # returns ACK or REJECT

    def cancel(self, order_id):
        self.pending_orders[order_id].cancel()
        request = jsonify({
            "type": "cancel",
            "order_id": order_id})
        s.send(request)
      # returns OUT even if order_id is invalid


class Strategy(object):
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

class Order(object):
    def __init__(self, order_id):
        self.order_id = order_id

        # possible states: CREATED, ACKED, CANCELLING
        self.state = 'CREATED'

    def handle_ack(self):
        self.state = 'ACKED'

    def cancel(self):
        self.state = 'CANCELLED'


class TradeOrder(Order):
    def __init__(self, order_id, symbol, direction, price, size):
        super(TradeOrder, self).__init__(order_id)
        self.symbol = symbol
        self.direction = direction
        self.price = price
        self.size = size

    def get_json_request(self):
        request = jsonify({
            "type": "add",
            "order_id": self.order_id,
            "symbol": self.symbol,
            "dir": self.direction,
            "price": self.price,
            "size": self.size})
        return request

class Strategy(object):
    def __init__(self, market, portfolio):
        self.market = market
        self.portfolio = portfolio

    def step(self):
        # Works with CORGE only for now
        cost = 100
        corge = self.market.stocks['CORGE']
        foo = self.market.stocks['FOO']
        bar = self.market.stocks['BAR']

        corgeAsk = corge.best_asks
        corgeBid = corge.best_bids
        fooAsk = foo.best_asks
        fooBid = foo.best_bids
        barAsk = bar.best_asks
        barBid = bar.best_bids
        if not all([len(x) > 0 for x in [corgeAsk, corgeBid, fooAsk, fooBid, barAsk, barBid]]):
            return
        corgeAsk = corge.best_asks[-1]
        corgeBid = corge.best_bids[-1]
        fooAsk = foo.best_asks[-1]
        fooBid = foo.best_bids[-1]
        barAsk = bar.best_asks[-1]
        barBid = bar.best_bids[-1]

        if corgeBid[0]-(0.3*fooAsk[0]+0.8*barAsk[0])>cost:
            num = min(fooAsk[1]/0.3, barAsk[1]/0.8, corgeBid[1])
            num = int(num / 10) * 10
            self.portfolio.buy('CORGE', corgeBid[0], num)
            self.portfolio.convert('SELL', num)
            self.portfolio.sell('FOO', fooAsk[0], num*3/10)
            self.portfolio.sell('BAR', barAsk[0], num*8/10)
        elif corgeAsk[0]-(0.3*fooBid[0]+0.8*barBid[0])>cost:
            num = min(fooBid[1]/0.3, barBid[1]/0.8, corgeAsk[1])
            num = int(num / 10) * 10
            self.portfolio.sell('CORGE', corgeAsk[0], num)
            self.portfolio.convert('BUY', num)
            self.portfolio.buy('FOO', fooBid[0], num*3/10)
            self.portfolio.buy('BAR', barBid[0], num*8/10)

class ConvertOrder(Order):
    def __init__(self, order_id, direction, size):
        super(ConvertOrder, self).__init__(order_id)
        self.symbol = 'CORGE'
        self.direction = direction
        self.size = size

    def get_json_request(self):
        request = jsonify({
            "type": "convert",
            "order_id": self.order_id,
            "symbol": "CORGE",
            "dir": self.direction,
            "size": self.size})
        return request


def calc_pnl(portfolio, stocks):
    return portfolio.balance + sum([stock.get_liquidated_value() for stock in stocks])


class mysocket(object):

    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock
        self.buf = ""
        self.log = []

    def connect(self, host, port):
        self.sock.connect((host, port))
        fcntl.fcntl(self.sock, fcntl.F_SETFL, os.O_NONBLOCK)

    def send(self, msg):
        print "Sending: ", msg
        self.sock.send(msg)

    def get_next(self):
        try:
            data = self.sock.recv(BUFFER_SIZE)
            if not data:
                return
        except socket.error, e:
            err = e.args[0]
            if not (err == errno.EAGAIN or err == errno.EWOULDBLOCK):
                # a "real" error occurred
                print e
                sys.exit(1)
        else:
            self.log.extend(data.strip().split('\n'))
            #print self.log
            return json.loads(self.log.pop(0))

def jsonify(p):
    return json.dumps(p) + '\n'


def send_hello(): #MUST ISSUE FIRST!!

    request = jsonify({\
                       "type": "hello", \
                       "team": "BANKMAKERS" })
    s.send(request)



if __name__ == '__main__':

    TEST = True
    TEST_INDEX = 0 # 0 = slow, 1 = normal, 2 = empty market
    if TEST:
        TCP_IP = '10.0.207.145'
    else:
        TCP_IP = 'real exchange ip'
    TCP_PORT = 25000 + TEST_INDEX
    BUFFER_SIZE = 4096
    s = mysocket()
    s.connect(TCP_IP, TCP_PORT)

    # t = Thread(target = s.recv)
    # t.start()
    # s.close() at some point

    SYMBOLS = ['FOO', 'BAR', 'BAZ', 'QUUX', 'CORGE']

    stocks = [Stock(symbol) for symbol in SYMBOLS]
    portfolio = Portfolio()

    market = Market(SYMBOLS)
    strategy = Strategy(market, portfolio)

    def handle(message):

        if not message:
            time.sleep(.001)
            return

        t = message['type']
        if t == 'hello':
            print message
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
            print "ACK:", message
            portfolio.handle_ack(message)

        if t == 'reject':
            print "REJECT:", message
            portfolio.handle_reject(message)

        if t == 'fill':
            print "FILL:", message
            portfolio.handle_fill(message)

        if t == 'out':
            print "OUT:", message
            portfolio.handle_out(message)



        print portfolio


#         # strategy.step()
# #	pass

    #listen for book updates...
    # if "type" == "book", put this JSON object in a "book" variable (analogous for "trade" type)
    send_hello()
    # portfolio.sell("BAR", 3000, 10)
    #portfolio.cancel(0)

    while True:
        # block until received message, and un-JSONify it
        message = s.get_next()
        handle(message)
        strategy.step()
