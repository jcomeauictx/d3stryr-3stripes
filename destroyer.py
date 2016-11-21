#!/usr/bin/env python3
import sys, os, configparser, logging, tempfile, multiprocessing, time
import datetime, select
logging.basicConfig(
    level=logging.DEBUG if __debug__ else logging.INFO,
    format='%(module)s %(asctime)s %(message)s')
# make sure we're in same directory as config.cfg
os.chdir(os.path.dirname(sys.argv[0]))
#Parse configuration file
CONFIG = configparser.ConfigParser()
CONFIG.read('config.cfg')
logging.debug('configuration sections: %s', CONFIG.sections())
USER = CONFIG['user']
HARVEST = CONFIG['harvest']
config = configparser.ConfigParser()
configFilePath = "config.cfg"
config.read(configFilePath)
#Get the size array
mySizes=config.get("user","mySizes").split(",")
#Strip leading and trailing whitespaces if present in each array index and store back into mySizes array
mySizes = [size.strip() for size in mySizes]
#Pull user info for locale
marketLocale=config.get("user","marketLocale")
parametersLocale=config.get("user","parametersLocale")
#Pull user info for masterPid
masterPid=config.get("user","masterPid")
#Token Harvesting info
manuallyHarvestTokens=config.getboolean("harvest","manuallyHarvestTokens")
numberOfTokens=config.getint("harvest","numberOfTokens")
harvestDomain=config.get("harvest","harvestDomain")
phpServerPort=config.get("harvest","phpServerPort")
captchaTokens=[]
#Pull 2captcha info
proxy2Captcha=config.get("user","proxy2Captcha")
apikey2captcha=config.get("user","apikey2captcha")
#Pull run parameters for handing inventory endpoints
useClientInventory=config.getboolean("user","useClientInventory")
useVariantInventory=config.getboolean("user","useVariantInventory")
#Pull run parameters for handing captchas
processCaptcha=config.getboolean("user","processCaptcha")
#Because end-users refuse to read and understand the config.cfg file lets go ahead
#and set processCaptcha to True if harvest is turned on.
if manuallyHarvestTokens:
  processCaptcha = True
processCaptchaDuplicate=config.getboolean("user","processCaptchaDuplicate")
#Pull info based on marketLocale
market=config.get("market",marketLocale)
marketDomain=config.get("marketDomain",marketLocale)
#Pull info based on parametersLocel
apiEnv=config.get("clientId","apiEnv")
clientId=config.get("clientId",parametersLocale)
sitekey=config.get("sitekey",parametersLocale)
#Pull info necessary for a Yeezy drop
duplicate=config.get("duplicate","duplicate")
cookies=config.get("cookie","cookie")
#Pull the amount of time to sleep in seconds when needed
sleeping=config.getint("sleeping","sleeping")
#Are we debugging?
debug=config.getboolean("debug","debug")
#Require end-user to press enter before terminating Chrome's browser window during ATC
pauseBeforeBrowserQuit=config.getboolean("debug","pauseBeforeBrowserQuit")

#Just incase we nee to run an external script.
scriptURL=config.get("script","scriptURL")

#Set this for parameters checking
hypedSkus=["AHypedSkuForAnAdidasShoe","AnotherHypedSkuForAnAdidasShoe"]

#Code to indicate a shitty exit from the script
exitCode = 1

#Lets try to keep a revision tracking via commit number.
revision="c+72"

if "nt" in os.name:
#We remove ANSI coloring for Windows
  class color:
    reset=''
    bold=''
    disable=''
    underline=''
    reverse=''
    strikethrough=''
    invisible=''
    black=''
    red=''
    green=''
    orange=''
    blue=''
    purple=''
    cyan=''
    lightgrey=''
    darkgrey=''
    lightred=''
    lightgreen=''
    yellow=''
    lightblue=''
    pink=''
    lightcyan=''
else:
#We use ANSI coloring for OSX/Linux
  class color:
    reset='\033[0m'
    bold='\033[01m'
    disable='\033[02m'
    underline='\033[04m'
    reverse='\033[07m'
    strikethrough='\033[09m'
    invisible='\033[08m'
    black='\033[30m'
    red='\033[31m'
    green='\033[32m'
    orange='\033[33m'
    blue='\033[34m'
    purple='\033[35m'
    cyan='\033[36m'
    lightgrey='\033[37m'
    darkgrey='\033[90m'
    lightred='\033[91m'
    lightgreen='\033[92m'
    yellow='\033[93m'
    lightblue='\033[94m'
    pink='\033[95m'
    lightcyan='\033[96m'

#In a threaded setup you can identify a printed line by its threadId - I just call it destroyerId
def d_(destroyerId=None):
  if destroyerId is not None:
    return "Destroyer # "+str(destroyerId).rjust(4," ")+" "+str(datetime.datetime.now().time().strftime("%I:%M:%S.%f")[:-3])
  else:
    return "Destroyer # "+revision+" "+str(datetime.datetime.now().time().strftime("%I:%M:%S.%f")[:-3])
def s_(string):
  return color.lightgrey+" ["+str(string).center(21," ")+"]"+color.reset+" "
#Color for exceptions
def x_(string):
  return color.lightred+" ["+str(string).center(21," ")+"]"+color.reset+" "
#Color for debugging
def z_(string):
  return color.orange+" ["+str(string).center(21," ")+"]"+color.reset+" "
#Colorize text with lightblue
def lb_(string):
  return color.lightblue+str(string)+color.reset
#Colorize text with lightred
def lr_(string):
  return color.lightred+str(string)+color.reset
#Colorize text with yellow
def y_(string):
  return color.yellow+str(string)+color.reset
#Colorize text with orange
def o_(string):
  return color.orange+str(string)+color.reset

def printRunParameters():
  print(d_()+s_("Market Locale")+lb_(marketLocale))
  print(d_()+s_("Parameters Locale")+lb_(parametersLocale))
  print(d_()+s_("Market")+lb_(market))
  print(d_()+s_("Market Domain")+lb_(marketDomain))
  print(d_()+s_("API Environment")+lb_(apiEnv))
  print(d_()+s_("Market Client ID")+lb_(clientId))
  print(d_()+s_("Market Site Key")+lb_(sitekey))
  print(d_()+s_("Captcha Duplicate")+lb_(duplicate))
  print(d_()+s_("Cookie")+lb_(cookies))
  print(d_()+s_("Process Captcha")+lb_(processCaptcha))
  print(d_()+s_("Use Duplicate")+lb_(processCaptchaDuplicate))
  print(d_()+s_("Product ID")+lb_(masterPid))
  print(d_()+s_("Desired Size")+lb_(mySizes))
  print(d_()+s_("Manual Token Harvest")+lb_(manuallyHarvestTokens))
  print(d_()+s_("Tokens to Harvest")+lb_(numberOfTokens))
  print(d_()+s_("Harvest Domain")+lb_(harvestDomain))
  print(d_()+s_("Harvest Port")+lb_(phpServerPort))
  print(d_()+s_("Sleeping")+lb_(sleeping))
  print(d_()+s_("Debug")+lb_(debug))
  print(d_()+s_("External Script URL")+lb_(scriptURL))
  print(d_()+s_("Pause Between ATC")+lb_(pauseBeforeBrowserQuit))

def checkParameters():
  nah = False
  if (marketLocale == "US") and (parametersLocale != "US"):
    print(d_()+z_("config.cfg")+lr_("Invalid marketLocale and parametersLocale combination."))
    nah = True
  if (useClientInventory) and (useVariantInventory):
    print(d_()+z_("config.cfg")+lr_("You should not set both inventory methods to True."))
  if (not manuallyHarvestTokens):
  #User is not token harvesting
    if (processCaptcha):
      if (apikey2captcha == "xXx"):
        print(d_()+z_("config.cfg")+lr_("You need a valid apikey2captcha if you want to use 2captcha service! Visit 2captcha.com"))
        nah = True
      if (proxy2Captcha == "localhost"):
        print(d_()+z_("config.cfg")+lr_("Unless you are testing - you should consider providing an IP whitelisted proxy for 2captcha to use."))
  else:
    #User is token harvesting
    if (not processCaptcha):
    #This should have been automatically set in the printRunParameters but lets check.
      print(d_()+z_("config.cfg")+lr_("You want to manually harvest tokens but you have not set processCaptcha to True. Much reading you have done."))
      nah = True
    if (numberOfTokens < 1):
      print(d_()+z_("config.cfg")+lr_("Your config.cfg makes no fucking sense. Why is numberOfTokens set to zero? And why are you requesting to harvest tokens?"))
      nah = True
    if (numberOfTokens > 5):
      print(d_()+z_("config.cfg")+lr_("You requested to harvest a large number of tokens. You wont be able to ATC until after you harvest all of the tokens. And tokens have a lifespan of ~ 120 seconds."))
    try:
      temp=int(phpServerPort)
    except:
      print(d_()+z_("config.cfg")+lr_("You have supplied an invalid phpServerPort value. Only numeric values accepted."))
      nah = True
  if (sleeping < 3):
      print(d_()+z_("config.cfg")+lr_("Your sleeping value is less than 3 seconds. It might not offer enough time between events."))
  if (masterPid in str(hypedSkus)):
    if (not processCaptchaDuplicate):
      print(d_()+z_("config.cfg")+lr_("This item is likely to make use of a captcha duplicate."))
    if ("neverywhere" in cookies):
      print(d_()+z_("config.cfg")+lr_("This item is likely to make use of a cookie."))
  if (not debug):
      print(d_()+z_("config.cfg")+lr_("debug is turned off. If you run into any issues dont bother tweeting them to me. Because I will ask you why debug is turned off."))

  if nah:
    #Flush stdout
    sys.stdout.flush()
    #Exit the script prematurely
    sys.exit(exitCode)

import random

def agent():
    '''
    Returns a random user-agent.

    >>> agent().startswith('Mozilla/5.0 ')
    True
    '''
    with open("useragent.txt") as infile:
        browsers = [s.rstrip() for s in infile.readlines()]
    return random.choice(browsers)

#We use time to sleep
import time
import json
import requests

requests.packages.urllib3.disable_warnings()

def getACaptchaTokenFrom2Captcha():
  session=requests.Session()
  session.verify=False
  session.cookies.clear()
  pageurl="http://www."+marketDomain
  print (d_()+s_("pageurl")+lb_(pageurl))
  while True:
    data={
     "key":apikey2captcha,
     "action":"getbalance",
     "json":1,
    }
    response=session.get(url="http://2captcha.com/res.php",params=data)
    JSON=json.loads(response.text)
    if JSON["status"] == 1:
      balance=JSON["request"]
      print (d_()+s_("Balance")+lb_("$"+str(balance)))
    else:
      print (d_()+x_("Balance"))
    CAPTCHAID=None
    proceed=False
    while not proceed:
      data={
       "key":apikey2captcha,
       "method":"userrecaptcha",
       "googlekey":sitekey,
       "proxy":proxy2Captcha,
       "proxytype":"HTTP",
       "pageurl":pageurl,
       "json":1
      }
      response=session.post(url="http://2captcha.com/in.php",data=data)
      JSON=json.loads(response.text)
      if JSON["status"] == 1:
        CAPTCHAID=JSON["request"]
        proceed=True
        print (d_()+s_("Captcha ID")+lb_(CAPTCHAID))
      else:
        print (d_()+x_("Response")+y_(response.text))
        print (d_()+x_("Sleeping")+y_(str(sleeping)+" seconds"))
        time.sleep(sleeping)
    print (d_()+s_("Waiting")+str(sleeping)+" seconds before polling for Captcha response")
    time.sleep(sleeping)
    TOKEN=None
    proceed=False
    while not proceed:
      data={
       "key":apikey2captcha,
       "action":"get",
       "json":1,
       "id":CAPTCHAID,
      }
      response=session.get(url="http://2captcha.com/res.php",params=data)
      JSON=json.loads(response.text)
      if JSON["status"] == 1:
        TOKEN=JSON["request"]
        proceed=True
        print (d_()+s_("Token ID")+lb_(TOKEN))
      else:
        print (d_()+x_("Response")+y_(response.text))
        print (d_()+x_("Sleeping")+y_(str(sleeping)+" seconds"))
        time.sleep(sleeping)
    data={
     "key":apikey2captcha,
     "action":"getbalance",
     "json":1,
    }
    response=session.get(url="http://2captcha.com/res.php",params=data)
    JSON=json.loads(response.text)
    if JSON["status"] == 1:
      balance=JSON["request"]
      print (d_()+s_("Balance")+lb_("$"+str(balance)))
    else:
      print (d_()+x_("Balance"))
    if TOKEN is not None:
      return TOKEN

def getClientResponse():
  headers = {
    'User-Agent':agent(),
  }
  session=requests.Session()
  session.verify=False
  session.cookies.clear()
  skus=masterPid+","
  for x in range(510,820,10):
    skus=skus+masterPid+"_"+str(x)+",";
  #Other countries will use US format like MX. They can just request US value for parametersLocale in config.cfg
  if parametersLocale == "US":
    clientStockURL="http://"+apiEnv+"-us-adidasgroup.demandware.net/s/adidas-"+marketLocale+"/dw/shop/v15_6/products/("+skus+")?client_id="+clientId+"&expand=availability,variations,prices"
  else:
    clientStockURL="http://"+apiEnv+"-store-adidasgroup.demandware.net/s/adidas-"+marketLocale+"/dw/shop/v15_6/products/("+skus+")?client_id="+clientId+"&expand=availability,variations,prices"
  if debug:
    print(d_()+z_("Debug")+o_(clientStockURL))
  response=session.get(url=clientStockURL,headers=headers)
  return response

def getVariantResponse():
  headers = {
    'User-Agent':agent(),
  }
  session=requests.Session()
  session.verify=False
  session.cookies.clear()
  #Not sure why I even bother making a case for Portugal if dude on twitter keeps telling it doesnt work. Da fuq is MLT?
  if market == "PT":
    variantStockURL="http://www."+marketDomain+"/on/demandware.store/Sites-adidas-"+marketLocale+"-Site/"+"MLT"+"/Product-GetVariants?pid="+masterPid
  else:
    variantStockURL="http://www."+marketDomain+"/on/demandware.store/Sites-adidas-"+marketLocale+"-Site/"+market+"/Product-GetVariants?pid="+masterPid
  if debug:
    print(d_()+z_("Debug")+o_(variantStockURL))
  response=session.get(url=variantStockURL,headers=headers)
  return response

def canonicalizeProductInfoClient(productJSON):
  #Initialize a dictionary.
  productInfo={}
  productInfo["productStock"]={}
  #Because of how we order the skus in clientStockURL 0-index is always masterPid info in the JSON response.
  try:
    data = productJSON["data"][0]
  except:
    print(d_()+x_("Parse Client JSON"))
    raise
  try:
    productInfo["productName"]=data["name"]
  except:
    productInfo["productName"]="/"
  try:
    productInfo["productColor"]=data["c_defaultColor"]
  except:
    productInfo["productColor"]="/"
  try:
    productInfo["productOrderable"]=data["inventory"]["orderable"]
  except:
    productInfo["productOrderable"]=False
  try:
    productInfo["productPrice"]=data["price"]
  except:
    productInfo["productPrice"]=0
  try:
    productInfo["productCount"]=productJSON["count"]-1
  except:
    productInfo["productCount"]=0
  try:
    productInfo["productATS"]=data["inventory"]["ats"]
  except:
    productInfo["productATS"]=0
  try:
    productInfo["productStockLevel"]=data["inventory"]["stock_level"]
  except:
    productInfo["productStockLevel"]=0
  """
  Because data[""c_sizeFTW"] and data["c_sizeSearchValue"] yield nonsense for some EU locales:
  Build a dictionary to convert adidas _XXX sizing to canonical sizing.
  """
  adidasSize2Size={}
  for variant in data["variation_attributes"][0]["values"]:
    adidasSize2Size[masterPid+"_"+variant["value"]]=variant["name"]

  """
  We could avoid:
    if data["id"] != masterPid:
  by using a for loop to iterate through:
    range(1,len(productJSON["data"])):
  But I doubt there is a performance hit here. Because this is only done once even if threading is introduce in the future.
  """
  for data in productJSON["data"]:
    if data["id"] != masterPid:
      try:
        productInfo["productStock"][adidasSize2Size[data["id"]]]={}
        productInfo["productStock"][adidasSize2Size[data["id"]]]["ATS"]=int(data["inventory"]["ats"])
        productInfo["productStock"][adidasSize2Size[data["id"]]]["pid"]=data["id"]
      except:
        print(d_()+x_("Client Inventory"))
  if debug:
    print(d_()+z_("Debug")+o_(json.dumps(productInfo,indent=2)))
  return productInfo

def canonicalizeProductInfoVariant(productJSON):
  #Creating a standard format of the data representation using a dictionary
  productInfo={}
  productInfo["productStock"]={}
  productInfo["productName"]="/"
  productInfo["productColor"]="/"
  productInfo["productOrderable"]="/"
  try:
    productInfo["productPrice"]=productJSON["variations"]["variants"][0]["pricing"]["standard"]
  except:
    productInfo["productPrice"]=0
  try:
    productInfo["productCount"]=len(productJSON["variations"]["variants"])
  except:
    productInfo["productCount"]=0
  productInfo["productATS"]=0
  try:
    for variant in productJSON["variations"]["variants"]:
      productInfo["productATS"]=productInfo["productATS"]+int(variant["ATS"])
      productInfo["productStock"][variant["attributes"]["size"]]={}
      productInfo["productStock"][variant["attributes"]["size"]]["ATS"]=int(variant["ATS"])
      productInfo["productStock"][variant["attributes"]["size"]]["pid"]=variant["id"]
  except:
    print(d_()+x_("Variant Inventory"))
  productInfo["productStockLevel"]=productInfo["productATS"]
  if debug:
    print(d_()+z_("Debug")+o_(json.dumps(productInfo,indent=2)))
  return productInfo

def getProductInfo():
  if useClientInventory:
    try:
      print(d_()+s_("Client Endpoint"))
      response=getClientResponse()
      productJSON=json.loads(response.text)
      productInfoClient=canonicalizeProductInfoClient(productJSON)
      return productInfoClient
    except:
      print(d_()+x_("Client Endpoint"))
      if debug:
        print(d_()+z_("Debug")+o_("Client Endpoint Response -"+response.text))
  #If we reached this point then useClientInventory didn't successfully return.
  #So lets proceed with useVariantInventory.
  try:
    print(d_()+s_("Variant Endpoint"))
    response=getVariantResponse()
    productJSON=json.loads(response.text)
    productInfoVariant=canonicalizeProductInfoVariant(productJSON)
    return productInfoVariant
  except:
    print(d_()+x_("Variant Endpoint"))
    if debug:
      print(d_()+z_("Debug")+o_("Variant Endpoint Response -"+response.text))
  #If we reached this point then useVariantInventory did not successfully return.
  #So lets produce at minimum size inventory.
  #We will refer to this as Fallback for productInfo (when both client and variant produces no inventory result).
  productInfoFallback={}
  productInfoFallback["productStock"]={}
  productInfoFallback["productName"]="/"
  productInfoFallback["productColor"]="/"
  productInfoFallback["productOrderable"]="/"
  productInfoFallback["productPrice"]=0
  productInfoFallback["productCount"]=-1
  productInfoFallback["productATS"]=-1
  productInfoFallback["productStockLevel"]=-1
  #US vs EU sizing seems to be off by 0.5 size
  if parametersLocale == "US":
    literalSize=4.5
    for variant in range(540, 750, 10):
      stringLiteralSize=str(literalSize).replace(".0","")
      productInfoFallback["productStock"][stringLiteralSize]={}
      productInfoFallback["productStock"][stringLiteralSize]["ATS"]=1
      productInfoFallback["productStock"][stringLiteralSize]["pid"]=masterPid+"_"+str(variant)
      literalSize=literalSize+.5
  else:
    literalSize=4.5
    for variant in range(550, 750, 10):
      stringLiteralSize=str(literalSize).replace(".0","")
      productInfoFallback["productStock"][stringLiteralSize]={}
      productInfoFallback["productStock"][stringLiteralSize]["ATS"]=1
      productInfoFallback["productStock"][stringLiteralSize]["pid"]=masterPid+"_"+str(variant)
      literalSize=literalSize+.5
  return productInfoFallback

def printProductInfo(productInfo):
  print(d_()+s_("Product Name")+lb_(productInfo["productName"]))
  print(d_()+s_("Product Color")+lb_(productInfo["productColor"]))
  print(d_()+s_("Price")+lb_(productInfo["productPrice"]))
  print(d_()+s_("Orderable")+lb_(productInfo["productOrderable"]))
  print(d_()+s_("ATS")+lb_(str(productInfo["productATS"]).rjust(6," ")))
  print(d_()+s_("Stock Level")+lb_(str(productInfo["productStockLevel"]).rjust(6," ")))
  print(d_()+s_("Size Inventory"))
  for size in sorted(productInfo["productStock"]):
    print(d_()+s_(size.ljust(5," ")+" / "+productInfo["productStock"][size]["pid"])+lb_(str(productInfo["productStock"][size]["ATS"]).rjust(6," ")))
  return

def add_to_carts(products=None):
    '''
    Using multiprocessing, add shoes to shopping carts of individual accounts
    '''
    if products is None:
        products = getProductInfo()
    accounts = USER.get('shoppingcarts', '').split(',')
    tokens = harvest_tokens(len(accounts))
    pipes = []
    done = 0
    for index in range(len(accounts)):
        if not tokens:
            logging.warn('No more tokens, skipping remaining accounts')
            break
        size, user, password, proxy = accounts[index].split(':')
        if size not in products['productStock']:
            logging.info('No stock of size %s is kept on this site', size)
            continue
        elif products['productStock'][size]['ATS'] == 0:
            logging.info('Size %s is not currently in stock', size)
            continue
        parent_end, child_end = multiprocessing.Pipe()
        process = multiprocessing.Process(
            target = add_to_cart,
            args = (
                products, index, size, (user, password),
                tokens.pop(0), proxy, child_end
            )
        )
        process.start()
        pipes.append(parent_end)
    while done < len(pipes):
        readable = select.select(pipes, [], [])[0]
        logging.debug('found readable pipes: %s', readable)
        for socket in readable:
            result = socket.recv()
            logging.info('result from child process: %s', result)
            done += 1

def add_to_cart(products, process_id, size, credentials, token, proxy, socket):
    '''
    Add size to cart, logging in afterwards if credentials are supplied
    '''
    logging.debug('starting browser')
    cache = tempfile.mkdtemp(suffix='.adidas.chrome')
    logging.debug('browser cache: %s', cache)
    browser = getChromeDriver(chromeFolderLocation=cache)
    browser.implicitly_wait(30)  # seconds to wait for page load after click
    logging.debug('ordering size %s', size)
    product_id = products['productStock'][size]['pid']
    addToCartChromeAJAX(product_id, token, browser)
    login(*credentials, browser, has_link=True)
    browser.quit()
    socket.send((process_id, size, 1))

def processAddToCart(productInfo):
  captchaTokensReversed=[]
  if manuallyHarvestTokens:
    harvestTokensManually()
    for index in range(0,len(captchaTokens)):
      captchaTokensReversed.append(captchaTokens.pop())
  logging.debug('starting browser')
  cache = tempfile.mkdtemp(suffix='.adidas.chrome')
  logging.debug('browser cache: %s', cache)
  browser = getChromeDriver(chromeFolderLocation=cache)
  browser.implicitly_wait(30)  # seconds to wait for page load after click
  username = USER.get('username', '')
  password = USER.get('password', '')
  logging.debug('beginning order loop')
  for mySize in mySizes:
    logging.debug('ordering size %s', mySize)
    try:
      mySizeATS=productInfo["productStock"][mySize]["ATS"]
      if mySizeATS == 0:
        logging.debug('no size %s available', mySize)
        continue
      print (d_()+s_("Add-To-Cart")+mySize+" : "+str(mySizeATS))
      pid=productInfo["productStock"][mySize]["pid"]
      #Check if we need to process captcha
      captchaToken=""
      if processCaptcha:
        #See if we have any manual tokens available
        if len(captchaTokensReversed) > 0:
          #Use a manual token
          captchaToken=captchaTokensReversed.pop()
          print (d_()+s_("Number of Tokens Left")+lb_(len(captchaTokensReversed)))
        else:
          #No manual tokens to pop - so lets use 2captcha
          captchaToken=getACaptchaTokenFrom2Captcha()
      addToCartChromeAJAX(pid,captchaToken,browser)
      login(username, password, browser, has_link=True)
      browser.quit()
    except KeyError:
      print (d_()+x_("Add-To-Cart")+lr_(mySize+" : "+"Not Found"))

#We use selenium for browser automation
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def getChromeDriver(chromeFolderLocation=None):
  chromedriver=None
  if "nt" in os.name:
  #Es ventanas?
    if os.path.isfile("chromedriver.exe"):
    #Lets check to see if chromedriver.exe is in the current directory
      chromedriver = "chromedriver.exe"
    elif os.path.isfile("C:\Windows\chromedriver.exe"):
    #Lets check to see if chromedriver.exe is in C:\Windows
      chromedriver = "C:\Windows\chromedriver.exe"
    else:
    #Lets see if the end-user will read this and fix their own problem before tweeting
      print (d_()+x_("Chromedriver.exe")+lr_("was not found in the current folder nor in C:\Windows"))
      sys.stdout.flush()
      sys.exit(exitCode)
  else:
  #Es manzanas?
    if os.path.isfile("./chromedriver"):
    #chromedriver should be in the current directory
      chromedriver = "./chromedriver"
    else:
      print (d_()+x_("chromedriver")+lr_("was not found in the current folder."))
      sys.stdout.flush()
      sys.exit(exitCode)
  os.environ["webdriver.chrome.driver"] = chromedriver
  chrome_options = Options()
  #We store the browsing session in ChromeFolder so we can manually delete it if necessary
  if chromeFolderLocation is not None:
    chrome_options.add_argument("--user-data-dir="+chromeFolderLocation)
  if False and USER.get('proxy', ''):
    '''
    with --proxy-server enabled, browser fails to work
    it works from the command line, but not with chromedriver
    '''
    chrome_options.add_argument('--proxy-server="%s"' % USER['proxy'])
  driver = webdriver.Chrome(chromedriver,chrome_options=chrome_options)
  return driver

def addToCartChromeAJAX(pid,captchaToken,browser=None):
  logging.debug('starting addToCartChromeAJAX()')
  if marketLocale == "PT":
    baseADCUrl="http://www."+marketDomain+"/on/demandware.store/Sites-adidas-"+"MLT"+"-Site/"+market
  else:
    baseADCUrl="http://www."+marketDomain+"/on/demandware.store/Sites-adidas-"+marketLocale+"-Site/"+market
  atcURL=baseADCUrl+"/Cart-MiniAddProduct"
  cartURL=baseADCUrl.replace("http://","https://")+"/Cart-Show"
  data={}
  #If we are processing captcha then add to our payload.
  if processCaptcha:
    data["g-recaptcha-response"]=captchaToken
  #If we need captcha duplicate then add to our payload.
  if processCaptchaDuplicate:
    #If cookies need to be set then add to our payload.
    if "neverywhere" not in cookies:
      headers["Cookie"]=cookies
    #Alter the atcURL for the captcha duplicate case
    atcURL=atcURL+"?clientId="+clientId
    #Add captcha duplicate  to our payload.
    data[duplicate]=captchaToken
  data["masterPid"]=masterPid
  data["pid"]=pid
  data["Quantity"]="1"
  data["request"]="ajax"
  data["responseformat"]="json"
  script="""
  $.ajax({
    url: '"""+atcURL+"""',
    data: """+json.dumps(data,indent=2)+""",
    method: 'POST',
    crossDomain: true,
    contentType: 'application/x-www-form-urlencoded',
    xhrFields: {
        withCredentials: true
    },
    complete: function(data, status, xhr) {
      console.log(status);
      console.log(data);
    }
  });"""
  externalScript=None
  if (len(scriptURL) > 0) and (".js" in scriptURL):
    externalScript="""
    $.ajax({
      url: '"""+scriptURL+"""',
      dataType: "script"
    });"""
  if debug:
    print(d_()+z_("Debug")+o_(json.dumps(data,indent=2)))
    print(d_()+z_("Debug")+o_(script))
    print(d_()+z_("Debug")+o_(externalScript))
  if not browser:
    cache = tempfile.mkdtemp(suffix='.adidas.chrome')
    logging.debug('browser cache: %s', cache)
    browser=getChromeDriver(chromeFolderLocation=cache)
  browser.get(baseADCUrl)
  if (len(scriptURL) > 0) and (".js" in scriptURL):
    print (d_()+s_("External Script"))
    browser.execute_script(externalScript)
  print (d_()+s_("ATC Script"))
  browser.execute_script(script)
  time.sleep(sleeping)
  browser.get(baseADCUrl+"/Cart-ProductCount")
  html_source = browser.page_source
  productCount=browser.find_element_by_tag_name('body').text
  productCount=productCount.replace('"',"")
  productCount=productCount.strip()
  if debug:
    print(d_()+z_("Debug")+o_("Product Count"+" : "+productCount))
    print(d_()+z_("Debug")+o_("\n"+html_source))
  if (len(productCount) == 1) and (int(productCount) > 0):
    results=browser.execute_script("window.location='"+cartURL+"'")
    time.sleep(10 if __debug__ else 0.5)
  else:
    print (d_()+x_("Product Count")+lr_(productCount))

  #Maybe the Product Count source has changed and we are unable to parse correctly.
  if pauseBeforeBrowserQuit:
    temp=input("Press Enter to Continue")

  #Need to delete all the cookes for this session or else we will have the previous size in cart
  return

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions

def activateCaptcha(driver):
  #Activate the catpcha widget
  iframe=driver.find_element_by_css_selector('iframe[src*="api2/anchor"]')
  driver.switch_to_frame(iframe)
  try:
    CheckBox=WebDriverWait(driver, sleeping).until(expected_conditions.presence_of_element_located((By.ID ,"recaptcha-anchor")))
  except:
    try:
      CheckBox=WebDriverWait(driver, sleeping).until(expected_conditions.presence_of_element_located((By.ID ,"recaptcha-anchor")))
    except:
      print (d_()+x_("Activate Captcha")+lr_("Failed to find checkbox"))
  CheckBox.click()

def checkSolution(driver,mainWindow):
  #Check to see if we solved the captcha
  solved=False
  while not solved:
    driver.switch_to.window(mainWindow)
    try:
      iframe=driver.find_element_by_css_selector('iframe[src*="api2/anchor"]')
    except:
      print (d_()+x_("Check Solution")+lr_("Failed to find checkbox"))
      return
    driver.switch_to_frame(iframe)
    try:
      temp=driver.find_element_by_xpath('//span[@aria-checked="true"]')
      print (d_()+s_("Check Solution")+lb_("Solved"))
      solved=True
    except:
      solved=False
    time.sleep(1)
  return solved

def getToken(driver,mainWindow):
  #We parse the token from the page
  token=None
  driver.switch_to.window(mainWindow)
  try:
    Submit=WebDriverWait(driver, sleeping).until(expected_conditions.presence_of_element_located((By.ID ,"submit")))
    Submit.click()
    time.sleep(1)
  except:
    print (d_()+x_("Captcha Submit")+lr_("Failed to click submit"))
  tokenElement=driver.find_element_by_css_selector('p#token')
  token=tokenElement.get_attribute("value")
  if token is not None:
    print (d_()+s_("Get Token")+lb_(token))
  return token

def harvest_tokens(number=1):
    '''
    Harvest captcha tokens from PHP page running locally

    These tokens can then be passed to Adidas within 120 seconds to bypass
    their captchas.

    *PLEASE NOTE* this does not click the "I am not a robot" checkbox, nor
    does it click the final <Submit> button, as the previous routine did.
    This was done to simplify the code, but has the added benefit of making
    the captchas much easier to solve, since the reCaptcha script detected
    the robotic clicking in the previous code, and as a result was much
    tougher scoring the puzzles.
    '''
    tokens = []
    elapsed = 0
    wait = 120 - 5  # need some time to purchase before tokens expire
    cache = tempfile.mkdtemp(suffix='.tokenharvest.chrome')
    logging.debug('browser cache: %s', cache)
    browser = getChromeDriver(chromeFolderLocation=cache)
    url = 'http://%s:%s/harvest.php' % (
        HARVEST['harvestDomain'], HARVEST['phpServerPort'])
    while len(tokens) < number:
        wait -= elapsed
        if wait < 3:  # minimum seconds needed to solve captcha
            break
        browser.implicitly_wait(wait)
        start = time.time()
        browser.get(url)
        try:
            token_element = browser.find_element_by_id('token')
        except selenium.common.exceptions.NoSuchElementException:
            logging.warn('Timed out trying to get token')
            break
        logging.debug('token_element found: %s', token_element)
        token = token_element.get_attribute("value")
        tokens.append(token)
        end = time.time()
        elapsed += end - start
    return tokens

def harvestTokensManually():
  print (d_()+s_("Manual Token Harvest")+lb_("Number of tokens harvested: "+str(len(captchaTokens))))
  cache = tempfile.mkdtemp(suffix='.tokenharvest.chrome')
  logging.debug('browser cache: %s', cache)
  browser=getChromeDriver(chromeFolderLocation=cache)
  url="http://"+harvestDomain+":"+phpServerPort+"/harvest.php"
  while len(captchaTokens) < numberOfTokens:
    browser.get(url)
    mainWindow = browser.current_window_handle
    try:
      activateCaptcha(driver=browser)
    except:
      print (d_()+x_("Page Load Failed")+lr_("Did you launch the PHP server?"))
      print (d_()+x_("Page Load Failed")+lr_("Falling back to 2captcha"))
      browser.quit()
      return
    solved=checkSolution(driver=browser,mainWindow=mainWindow)
    token=getToken(driver=browser,mainWindow=mainWindow)
    if token is not None:
      if len(captchaTokens) == 0:
        startTime = time.time()
      captchaTokens.append(token)
      print (d_()+s_("Token Added"))
      print (d_()+s_("Manual Token Harvest")+lb_("Number of tokens harvested: "+str(len(captchaTokens))))
    currentTime = time.time()
    elapsedTime = currentTime - startTime
    print (d_()+s_("Total Time Elapsed")+lb_(str(round(elapsedTime,2)) + " seconds"))
  browser.quit()

def login(username=None, password=None, browser=None, has_link=False):
    '''
    Login to Adidas

    Pass in a WebDriver object as browser if one is already in use.

    Set has_link to True if the currently loaded page is expected to already
    have a login link.
    '''
    if not (username and password):
        logging.warn('Cannot login. No username/password in config.cfg')
        return False
    if browser is None:
        cache = tempfile.mkdtemp(suffix='.adidas.chrome')
        logging.debug('browser cache: %s', cache)
        browser = getChromeDriver(chromeFolderLocation=cache)
        browser.implicitly_wait(30)
    if not has_link:
        browser.get('https://www.%s/' % marketDomain)
    login_link = browser.find_element_by_xpath(
        '//*[@class="selfservice-link-login"]')
    if login_link.tag_name != 'a':
        logging.debug('Trying to find a.href under %s', login_link.tag_name)
        login_link = login_link.find_element_by_xpath('./a')
    login_link.click()
    browser.switch_to_frame('loginaccountframe')
    inputs = browser.find_elements_by_tag_name('input')
    logging.debug('Found inputs: %s', [i.get_attribute('name') for i in inputs])
    input_username = browser.find_element_by_name('username')
    input_password = browser.find_element_by_name('password')
    submit = browser.find_element_by_name('signinSubmit')
    logging.debug('Found login page successfully, so logging in')
    input_username.send_keys(username)
    input_password.send_keys(password)
    submit.click()
    logging.debug('Waiting for login success or failure')
    try:
        logout = browser.find_element_by_xpath('//div[@class="not_user"]')
    except selenium.common.exceptions.NoSuchElementException:
        logging.debug('Could not find `logout` link container')
        logout = None
    return logout is not None

if __name__ == '__main__':
    # allows for testing individual routines from command line
    if len(sys.argv) > 1:
        command = sys.argv[1]
    else:
        command = 'add_to_carts'
    if command in globals():
        print(eval(command)(*sys.argv[2:]))
    else:
        logging.critical('No such routine %s', command)
