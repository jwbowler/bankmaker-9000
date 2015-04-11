import time
import json
import socket



class Book:
    def update(book_dict):
        self.symbol = book_dict['symbol']
        self.buy = book_dict['buy']
        self.sell = book_dict['sell']
        
        
class Stock:

    ##has: current book, list of transactions, list of historical best bids and best asks
    def __init__(self, symbol):
        self.symbol = symbol
        self.book = Book() # current book
        self.trades = []
        
        # lists of (price, size) tuples
        self.best_bids = []
        self.best_asks = []
        
    # type = book, trade, fill
    def update(self, update_dict):
        if update_dict['type'] == 'book':
            self.book.update(update_dict)
            
            if len(update_dict['buy']) > 0:
                assert len(update_dict['buy'][0]) == 2
                new_best_bid = (time.time(), update_dict['buy'][0])
                self.best_bids.append[update_dict['buy'][0]]
            
            if len(update_dict['sell']) > 0:
                assert len(update_dict['sell'][0]) == 2
                new_best_ask = (time.time(), update_dict['sell'][0])
                self.best_asks.append[update_dict['sell'][0]]
            
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
            

                
       
            
class Portfolio:
    
    def __init__(self, symbols):
        self.balance = 0
        self.positions = {symbol: 0 for symbol in SYMBOLS}
        self.numrequests = 0
        
        
    def hello(): #MUST ISSUE FIRST!!
    
        request = json.dumps({\
            "type": "hello", \
            "team": TEAM_NAME })
        s.send(request)
        return json.loads(s.recv(BUFFER_SIZE))
    
    
    def buy(symbol, price, size): 
        request = json.dumps({\
            "type": "add", \
            "order_id": self.numrequests, \
            "symbol": symbol, \
            "dir": "BUY", \
            "price": price, \
            "size": size})
        self.numrequests += 1
        s.send(request)
        return s.recv(json.loads(BUFFER_SIZE))
            
        
    def sell(symbol, price, size):
        request = json.dumps({\
            "type": "add", \
            "order_id": self.numrequests, \
            "symbol": symbol, \
            "dir": "SELL", \
            "price": price, \
            "size": size})
        self.numrequests += 1
        s.send(request)
        return s.recv(json.loads(BUFFER_SIZE))
    
    def convert(dir, size):
        request = json.dumps({\
            "type": "convert", \
            "order_id": self.numrequests, \
            "symbol": "CORGE", \
            "dir": dir, \
            "size": size})
        self.numrequests += 1
        s.send(request)
        return s.recv(json.loads(BUFFER_SIZE))
        
      # dir = “BUY” or “SELL”, buy = convert to CORGE, sell = convert from CORGE
      # size must be a multiple of 10!!!
      # fixed cost of 100 per conversion (regardless of size)
      # one CORGE = 0.3 FOO + 0.8 BAR
      # returns ACK or REJECT
    
    def cancel(order_id):
        request = json.dumps({\
            "type": "cancel", \
            "order_id": order_id})
        s.send(request)
        s.recv(json.loads(BUFFER_SIZE))
      # returns OUT even if order_id is invalid

        
class Trade:
    def __init__(self, trade_dict):
        self.symbol = trade_dict.symbol
        self.price = trade_dict.price
        self.size = trade_dict.size
   


def calc_pnl(portfolio, stocks):
    return portfolio.balance + sum([stock.get_liquidated_value() for stock in stocks])
        
        
        
def handle(message):
    t = message['type']
    
    if t == 'hello':
        pass
    
    if t == 'market_open':
        pass
    
    if t == 'error':
        pass
    
    if t == 'book':
        pass
    
    if t == 'trade':
        pass
    
    if t == 'ack':
        pass
    
    if t == 'reject':
        pass
    
    if t == 'fill':
        pass
        
    if t == 'out':
        pass
        


if __name__ == '__main__':
    
    TEST = True
    TEST_INDEX = 0 # 0 = slow, 1 = normal, 2 = empty market
    if TEST:
        TCP_IP = '10.0.207.145'
    else:
        # TCP_IP = 'real exchange ip'
    TCP_PORT = 25000 + TEST_INDEX
    BUFFER_SIZE = 1024
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))
    
    # s.close() at some point
    
    SYMBOLS = ['FOO', 'BAR', 'BAZ', 'QUUX', 'CORGE']
    TEAM_NAME = 'BANKMAKERS'
    
    stocks = [Stock(symbol) for symbol in SYMBOLS]
    portfolio = Portfolio()
    
    
    #listen for book updates... 
    # if "type" == "book", put this JSON object in a "book" variable (analogous for "trade" type)
        
    