import yfinance as yf
import re
import requests
import os
from textblob import TextBlob
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import pickle


#returns stock with highest value from list passed into it
def getHighestValueStock(symbols):

  os.system('cls' if os.name == 'nt' else 'clear')
  print("loading...")
  
  highest_valued_symbol = None
  highest_valued_price = 0

  for symbol in symbols:
      stock = yf.Ticker(symbol)
      current_price = stock.info["dayHigh"]
      if current_price > highest_valued_price:
          highest_valued_price = current_price
          highest_valued_symbol = symbol

  
  return highest_valued_symbol


#returns true if a symbol exists in yfinance
def isSymbolReal(symbol):
  try:
    stock = yf.Ticker(symbol)
    info = stock.info
    if info['dayHigh'] is not None:
      return True
    else:
        return False
  except:
      return False


#loop through and look for caps
def retrieveSymbols(text):
  pattern = r'\b[A-Z]{2,7}\b'
  matches = re.findall(pattern, text)
  stockSymbols = []
  for symbol in matches:
    if isSymbolReal(symbol):
      stockSymbols.append(symbol)

  return getHighestValueStock(stockSymbols)


#returns ["<Content>", "<Symbol>"]
def makeListOfPostsAndSymbols(jsonList):
  listOfPosts = []

  for subR in jsonList:
    for post in subR.json()['data']['children']:
      listOfPosts.append(post['data']['selftext'])

  listOfPostsAndSymbols = []

  for i, item in enumerate(listOfPosts):
    #if it doesn't find any symbols
    if item == None:
      listOfPosts.remove(item)
    else:
      sublist = [item, retrieveSymbols(item)]
      listOfPostsAndSymbols.append(sublist)

  return listOfPostsAndSymbols


#authorizes the reddit api
def authorize():
  auth = requests.auth.HTTPBasicAuth('jVA7q0gu_dXAv3FXe-f1NA',
                                     'GBTpB2OZSIY8ZXSz44_EHojgEiUcWg')

  data = {
    'grant_type': 'password',
    'username': 'BananasOnComputers',
    'password': 'JlOrDG2qfe51'
  }

  headers = {'User-Agent': 'appuller/0.0.1'}

  # send our request for an OAuth token
  res = requests.post('https://www.reddit.com/api/v1/access_token',
                      auth=auth,
                      data=data,
                      headers=headers)

  # convert response to JSON and pull access_token value
  TOKEN = res.json()['access_token']

  # add authorization to our headers dictionary
  headers = {**headers, **{'Authorization': f"bearer {TOKEN}"}}

  # while the token is valid (~2 hours) we just add headers=headers to our requests
  requests.get('https://oauth.reddit.com/api/v1/me', headers=headers)

  stocksSR = requests.get("https://oauth.reddit.com/r/stocks/hot",
                          headers=headers, params={'limit': '50'})
  wsbSR = requests.get("https://oauth.reddit.com/r/wallstreetbets/hot",
                       headers=headers, params={'limit': '50'})
  stocksAndTradingSR = requests.get(
    "https://oauth.reddit.com/r/StocksAndTrading/hot", headers=headers, params={'limit': '50'})

  return [stocksSR, wsbSR, stocksAndTradingSR]


#removes any list None as the second value
def removeNoneSublists(list_of_lists):
    filtered_list = []
    for sub_list in list_of_lists:
        if sub_list[1] is not None:
            filtered_list.append(sub_list)
    return filtered_list

#The user selects a stock from the list (sorted in order) - returns string
def select_stock(lst):
    # Extract unique symbols from the input list
    symbols = list(set([l[1] for l in lst]))

    # Get the market price for each symbol using yfinance
    prices = []
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            price = data["Close"][0]
            prices.append((symbol, price))
        except:
            continue

    # Sort the prices in descending order
    prices.sort(key=lambda x: x[1], reverse=True)

    # Display the top 10 symbols and prices
    print("Top 10 symbols reddit users are talking about by price:")
    for i, (symbol, price) in enumerate(prices[:10]):
        print(f"{i+1}. {symbol}: ${price:.2f}")

    # Ask the user to select a symbol
    while True:
        try:
            choice = int(input("Select a symbol (enter the corresponding number): "))
            if 1 <= choice <= 10:
                selected_symbol = prices[choice-1][0]
                print('You selected ' + selected_symbol + '.')
                return selected_symbol
            else:
                print("Invalid selection. Please choose a number between 1 and 10.")
        except ValueError:
            print("Invalid input. Please enter a number.")


#retreives sentiment score and compares it to see if it's positive/negative - returns string
def goodOrBad(posts, symbol):
  
  sentimentValue = 0
    
  for post in posts:
    if post[1] == symbol:
      sentiment_score = TextBlob(post[0]).sentiment.polarity
      sentimentValue += sentiment_score

  endString = ""
  
  if sentimentValue>0:
    endString += ('People are talking positively about '  + userSelectedStock + '.')
  elif sentimentValue==0:
    endString += ('People are neutral about ' + userSelectedStock + '.')
  else:
    endString += ('People are talking negatively about ' + userSelectedStock + '.')

  return (endString + "\nCalculated Sentiment Value: " + str(sentimentValue))


#graphs the stock data for the past year using matplotlib
def plotStockPrice(stock_symbol):
    # Calculate the start and end dates for the past year
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')

    # Download data from Yahoo Finance for the past year
    stock_data = yf.download(stock_symbol, start=start_date, end=end_date)

    # Extract the adjusted close price and date
    stock_price = stock_data['Adj Close']
    date = stock_price.index
    
    # Plot the stock price data as a line graph
    plt.plot(date, stock_price)
    plt.xlabel('Date')
    plt.ylabel('Stock Price (USD)')
    plt.title(f'Stock Price of {stock_symbol} Over the Past Year')
    
    # Display the plot in the console
    plt.show(block=False)


#OPTIONAL - if user wants to display graph or not
def askGraph():
  answer=''
  while (answer!='n') and (answer!='y'):
    answer=input('Do you want to display the graph of recent stock prices for this symbol? (y/n) ')
    if answer=='y':
      plotStockPrice(userSelectedStock)
    elif answer!='n':
      print('Invalid response.  Please enter "y" or "n" ')

#asks the user if they want to run the entire program again
def repeatProgramLoop():
  answer=''
  while (answer!=1) and (answer!=0):
    answer=input("Do you want to keep using the program? y/n: ")
    if answer=='y':
      return 1
    elif answer=='n':
      return 0
    else:
      print('Invalid response.  Please enter "y" or "n" ')
      
#initial program sequence - either loads information from pickle file or retrieves it from reddit api
def startProgram():
  answer=''
  while (answer!='1') and (answer!='2'):
    answer=input("Do you want to load new reddit posts (1) or use last loaded posts (2): ")
    if (answer!='1') and (answer!='2'):
      print('Invalid response.  Please enter "1" or "2"')
  if answer=='1':
    #initial list creation
    listOfJson = authorize()
    listPostsAndSymbols = makeListOfPostsAndSymbols(listOfJson)
    listPostsAndSymbols = removeNoneSublists(listPostsAndSymbols)
    #save list to pickle file (overwrites)
    with open("list.pkl", "wb") as f:
      pickle.dump(listPostsAndSymbols, f)
  elif answer=='2':
    #load pickle file
    with open("list.pkl", "rb") as f:
      listPostsAndSymbols = pickle.load(f)
  return listPostsAndSymbols


if __name__ == "__main__":
  onOff=1
  while onOff==1:
    plt.close()
    os.system('cls' if os.name == 'nt' else 'clear')
    
    listPostsAndSymbols = startProgram() 
    userSelectedStock = select_stock(listPostsAndSymbols) 
  
    print(goodOrBad(listPostsAndSymbols, userSelectedStock))
  
    askGraph()
  
    onOff=repeatProgramLoop()

  


