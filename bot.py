import telegram.ext
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException
import constants as c
from pprint import pprint
import os

PORT = int(os.environ.get('PORT', 49705))

# getting constants
api_key = c.API_KEY
api_secret = c.API_SECRET
TOKEN = c.TOKEN

#initializing Binance client
client = Client(api_key, api_secret, testnet=True)

#Get futures pair percesions from binance
info = client.futures_exchange_info() # request info on all futures symbols
symbols_n_precision = dict()
for item in info['symbols']: 
    symbols_n_precision[item['symbol']] = item['quantityPrecision'] # not really necessary but here we are...

#Creating The trade class t create and execute a trade
class Trade():
    def __init__(self, mode, leverage, pair, price, SL, TP):
        self.mode = mode
        self.leverage = int(leverage)
        self.symbol = pair
        self.price = float(price)
        self.SL = float(SL)
        self.TP = float(TP)
        self.trade_size_in_dollars = 1000
        self.order_amount = self.trade_size_in_dollars / self.price
    
    def getOrderAmount(self, x):
        try:
            #Get futures pair percesions from binance
            info = client.futures_exchange_info() # request info on all futures symbols
            symbols_n_precision = dict()
            for item in info['symbols']: 
                symbols_n_precision[item['symbol']] = item['quantityPrecision'] # not really necessary but here we are...
            self.precision = symbols_n_precision[self.symbol]
            print(self.precision)
            self.precise_order_amount = "{:0.0{}f}".format(self.order_amount*x, self.precision)
            return float(self.precise_order_amount)
        except KeyError as e:
            print(e)
            print(f'{self.symbol}Choose a valid PAIR Symbol')

    def execute(self):
        client.futures_change_leverage(symbol=self.symbol, leverage=self.leverage)
        if self.mode in ['buy', 'BUY', 'Buy']:
            try:
                order1 = client.futures_create_order(
                    symbol = self.symbol,
                    type = 'LIMIT',
                    timeInForce = 'GTC',  # Can be changed - see link to API doc below
                    price = float(self.price),  # The price at which you wish to buy/sell, float
                    side = 'BUY',  # Direction ('BUY' / 'SELL'), string
                    quantity = self.getOrderAmount(1),  # Number of coins you wish to buy / sell, float
                    isIsolated = 'TRUE'
                )
                stopLoss = client.futures_create_order(
                            symbol = self.symbol,
                            type = 'STOP_MARKET',
                            side = 'SELL',
                            stopPrice = self.SL,
                            timeInForce = 'GTC',
                            closePosition = True
                            )
                takeProfit = client.futures_create_order(
                            symbol = self.symbol,
                            type = 'TAKE_PROFIT_MARKET',
                            side = 'SELL',
                            stopPrice = self.TP,
                            timeInForce = 'GTC',
                            closePosition = True
                            )
            except BinanceAPIException as e:
                print(e)
                client.futures_cancel_all_open_orders(symbol=self.symbol)
                return e
 
        elif self.mode in ['Sell', 'SELL', 'sell']:
            try:
                order1 = client.futures_create_order(
                    symbol = self.symbol,
                    type = 'LIMIT',
                    timeInForce = 'GTC',  # Can be changed - see link to API doc below
                    price = float(self.price),  # The price at which you wish to buy/sell, float
                    side = 'SELL',  # Direction ('BUY' / 'SELL'), string
                    quantity = self.getOrderAmount(self.leverage),  # Number of coins you wish to buy / sell, float
                    isIsolated = 'TRUE'
                )
                stopLoss = client.futures_create_order(
                            symbol = self.symbol,
                            type = 'STOP_MARKET',
                            side = 'BUY',
                            stopPrice = float(self.SL),
                            timeInForce = 'GTC',
                            closePosition = True
                            )
                takeProfit = client.futures_create_order(
                            symbol = self.symbol,
                            type = 'TAKE_PROFIT_MARKET',
                            side = 'BUY',
                            stopPrice = float(self.TP),
                            timeInForce = 'GTC',
                            closePosition = True
                            )
            except  BinanceAPIException as e:
                print(e)
                client.futures_cancel_all_open_orders(symbol=self.symbol)
                return e
        else:
            return 'Enter a Valid mode BUY/SELL for LONG/SHORT'
        return {'Order': order1, 'SL': stopLoss, 'TP': takeProfit}


def updateOrder(var):
    ''' Update the current Order to trade '''
    global Order
    Order = var

updateOrder('')

def start(update, context):
    ''' Bot Greeting '''
    update.message.reply_text('Hey, Trader! See /help for How to use.')

def help(update, context):
    '''This is a help command'''
    update.message.reply_text('''
    This is a trading bot for binance futures. The following commands are available:
    */start: simple greeting.\n
    */help: this message.\n
    */createOrder: Create a LONG/SHORT futures order with stopLoss and takeProfit.\nUSAGE: /createOrder [BUY/SELL] [leverage X] [tickerPair] [PRICE] [SL] [TP].\nExample: long 20X position on BNBUSDT limit price 450 stopLoss 430 takeProfit 470.\nThe command would be: /createOrder BUY 20 BNBUSDT 450 430 470.\n
    */trade: executes the created order.\nFirst you need to create an order with /createOrder.\n
    */cancelAllOpen: Cancel all non-FILLED open orders for a symbole.\nUSAGE: /cancelAllOpen [tickerPair. \nExample: /cancelAllOpen BNBUSDT.\n
    */cancelOpenOrder: Cancel a non-FILLED open order for a symbole by orderID.\nUSAGE: /cancelOpenOrder [tickerPair] [orderID*].\nExample /cancelOpenOrder BNBUSDT 24698765.\nNOTE: you will get the order ID when executing it with /trade.
    ''')

def createOrder(update, context):
    '''Create a LONG/SHORT futures order with stopLoss and takeProfit. And adds it to the current temp order to trade.'''
    try:
        mode = str(context.args[0])
        leverage = int(context.args[1])
        pair = str(context.args[2])
        price = float(context.args[3])
        stopLoss = float(context.args[4])
        takeProfit = float(context.args[5])
        global trade
        trade = Trade(mode, leverage, pair, price, stopLoss, takeProfit)

        if mode in ['buy', 'BUY', 'Buy']:
            quantity = trade.getOrderAmount(1)
        else:
            quantity = trade.getOrderAmount(leverage)
        
        order = {
                'mode': mode,
                'leverage X': leverage,
                'pair': pair,
                'price': price,
                'stopLoss': stopLoss,
                'takeProfit': takeProfit,
                'Quantity': quantity,
        }
        updateOrder(order)
        mssg = '\n'.join([f"{key}: {val}" for key, val in order.items()])
        update.message.reply_text(f"{mssg}\n\nThe Above order is created.\nType /trade to Execute this trade. OR update it by Overwriting it with an other order using the same /createOrder commande.\nCheck /help for more info")
    except (ValueError, KeyError, IndexError, BinanceAPIException) as e:
        print(e)
        update.message.reply_text('Invalid Order. Please create a valid order. See /help for more info')
        

def trade(update, context):
    ''' this function executes the current temp order. And clears the temp order.'''
    if Order == '':
            update.message.reply_text('Please create an order before executing a Trade. See /help for more info')
    elif Order['Quantity'] == 0:
        update.message.reply_text(f"{Order['Quantity']} Insufficient Quantity. Check the minimum quantity for {Order['pair']} On Binance.")
    else:
        try:
            ordersStatus = trade.execute()
            if type(ordersStatus) == type(dict()):
                mssg = '\n'.join([f"{key}: {val}" for key, val in Order.items()])
                update.message.reply_text(f"This Order:\n\n{mssg}\n\nIS PLACED CHECK YOUR BINANCE ORDERS")
                updateOrder('')
                for key, val in ordersStatus.items():
                    update.message.reply_text(f"{key}: {val['orderId']}\n")
            else:
                mssg = ordersStatus
                update.message.reply_text(f"{mssg}\n\nCheck the minimum quantity for {Order['pair']}.")
                updateOrder('')
        except BinanceAPIException as e:
            print(e)
            update.message.reply_text(f"{e}")

def cancelAllOpen(update, context):
    '''Cancel all non-FILLED open orders for a symbole'''
    try:
        symbole = context.args[0]
        cancel = client.futures_cancel_all_open_orders(symbol=symbole)
        update.message.reply_text(f"{cancel}\nAll {symbole} open orders are canceled. Check BINANCE OPEN POSITIONS IF YOU WANT TO CLOSE THEM.")
        pprint(cancel)
    except (KeyError, BinanceAPIException) as e:
        print(e)
        update.message.reply_text('Invalid argument. Check /help fr more info.')

def cancelOpenOrder(update, context):
    ''' Cancel a non-FILLED open order for a symbole by ID '''
    try:
        symbole = context.args[0]
        orderId = context.args[1]
        cancel = client.futures_cancel_order(symbol=symbole, orderId=orderId)
        update.message.reply_text(f"{cancel['orderId']}|{cancel['symbol']}: {cancel['status']} TYPE: {cancel['type']}\nThe order {orderId} of {symbole} is canceled. Check BINANCE OPEN POSITIONS IF YOU WANT TO CLOSE THEM.")
        pprint(cancel)
    except (KeyError, BinanceAPIException) as e:
        print(e)
        if 'Unknown order sent' in e:
            update.message.reply_text(f'{orderId} is ')
        else:
            update.message.reply_text('Invalid argument. Check /help fr more info.')

#initialize updater and dispatcher
updater = telegram.ext.Updater(TOKEN, use_context=True)
disp = updater.dispatcher

#handlBotCommandes
disp.add_handler(telegram.ext.CommandHandler('start', start))
disp.add_handler(telegram.ext.CommandHandler('help', help))
disp.add_handler(telegram.ext.CommandHandler('createOrder', createOrder))
disp.add_handler(telegram.ext.CommandHandler('trade', trade))
disp.add_handler(telegram.ext.CommandHandler('cancelAllOpen', cancelAllOpen))
disp.add_handler(telegram.ext.CommandHandler('cancelOpenOrder', cancelOpenOrder))

#activating the Bot
updater.start_webhook(listen="0.0.0.0",
                      port=int(PORT),
                      url_path=TOKEN,
                      webhook_url = 'https://cryptic-coast-74798.herokuapp.com/' + TOKEN)

# updater.start_polling()
updater.idle()
