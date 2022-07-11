from selenium import webdriver
from selenium.common.exceptions import JavascriptException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller


from linkpreview import Link, LinkPreview, LinkGrabber
import requests
from requests import get
import shutil

from pathlib import Path

from datetime import datetime
import time
import os
import sys
import ssl
import argparse
import re
import base64
import magic
import urllib.request
import json


whatsappLink = "https://web.whatsapp.com/"
wait = None
choice = None
contactNumber = None
contactName = None
variables = []
encodedMedia = None
mediaName = None
hyperlink = None
success = []
failed = []
whatsappNumbers = []
nonWhatsappNumbers = []
logFile = None
browser = None
linkTitle = None
linkDescription = None
linkImage = None
if(sys.platform == "linux"):
    osUser = os.getenv('USER')
    pathToAccountData = "/home/" + osUser + "/.whatsArc/Accounts"
    pathToAppData = "/home/" + osUser + "/.whatsArc"
    fileSelectorPath = "/home/" + osUser
else:
    osUser = os.getenv('USERPROFILE')
    pathToAccountData = os.getenv('LOCALAPPDATA')+'\\whatsArc\\Accounts'
    pathToAppData = os.getenv('LOCALAPPDATA')+'\\whatsArc'
    fileSelectorPath = osUser+"\\Desktop"
account = "Default"
accounts = []
isRotate = False
rotateInterval = 100

parser = argparse.ArgumentParser(description='PyWhatsapp Guide')
# parser.add_argument('--chrome_driver_path', action='store', type=str, default='./chromedriver.exe',help='chromedriver executable path (MAC and Windows path would be different)')
parser.add_argument('--message', action='store', type=str,default='', help='Enter the msg you want to send')
parser.add_argument("--ignore-certificate-errors")
parser.add_argument('--remove_cache', action='store', type=str, default='False', help='Remove Cache | Scan QR again or Not')
args = parser.parse_args()

if args.remove_cache == 'True':
    shutil.rmtree(pathToAccountData+'\\'+account)
message = None if args.message == '' else args.message



def encodeMedia(mediaPath,thumb=False):
    global encodedMedia,mediaName,linkImage
    
    mime = magic.Magic(mime=True)
    mediaName = Path(mediaPath).name

    with open(mediaPath, "rb") as mediaFile:
        if thumb:
            linkImage = (base64.b64encode(mediaFile.read()).decode("utf-8"))
        else:
            encodedMedia = ("data:" + mime.from_file(mediaPath) + ";" + "base64," + base64.b64encode(mediaFile.read()).decode("utf-8"))

# def importContacts(csvPath):
#     print(csvPath)
#     global contactNumber, contactName, variables

#     # Create a dataframe from
#     # colnames = ['name', 'mobile','VAR1','VAR2','VAR3','VAR4','VAR5']
#     data = pd.read_csv(csvPath).fillna("")
#     print(data)

#     # Clear lists
#     contactName = contactNumber = variables = []
    
#     contactName = data.name.tolist()
#     # contactName.pop(0)
#     contactNumber = list(map(str,data.mobile.tolist()))
#     # contactNumber.pop(0)
#     variables.append(data.VAR1.tolist())
#     variables.append(data.VAR2.tolist())
#     variables.append(data.VAR3.tolist())
#     variables.append(data.VAR4.tolist())
#     variables.append(data.VAR5.tolist())

#     prospect = {}
#     prospect["name"] = contactName
#     prospect["mobile"] = contactNumber
#     prospect["variables"] = variables

#     return prospect

def whatsappLogin():
    global wait, browser, whatsappLink,account

    chromedriver_autoinstaller.install()
    chrome_options = Options()
    chrome_options.add_argument(f'--user-data-dir={pathToAccountData}/{account}')
    chrome_options.set_capability('unhandledPromptBehavior', 'accept')
    # chrome_options.add_argument('headless')
    browser = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(browser, 600)
    browser.get(whatsappLink)
    browser.set_window_position(0, 0)
    browser.set_window_size(500, 500)
    # browser.maximize_window()
    print("QR scanned")    
    try:
        WebDriverWait(browser, 600).until(EC.presence_of_element_located((By.XPATH, '//*[@id="app"]/div/div/div[4]/div/div/div[1]/span')))
        with open(pathToAppData+"\\wapi.js",'r') as script:
            browser.execute_script(script.read())
            print('script initialized')
            # time.sleep(180)
        # print('sleeping')
        # time.sleep(180)
    except:
        wait = WebDriverWait(browser, 600)
        browser.get(whatsappLink)

def sender(index,number):
    global choice,success,failed,hyperlink,isRotate,rotateInterval,browser

    if choice == "onlyMessage":
        if status := sendOnlyMessage(index,number):
            failed.append("{0} - {1}".format(contactName[index],number))
            return status
        else:
            success.append("{0} - {1}".format(contactName[index],number))
            return 'sent!'
    elif choice == "onlyMedia":
        if status := sendMedia(index,number):
            failed.append("{0} - {1}".format(contactName[index],number))
            return status
        else:
            success.append("{0} - {1}".format(contactName[index],number))
            return 'sent!'
    elif choice == "document":
        if status := sendMedia(index,number):
            failed.append("{0} - {1}".format(contactName[index],number))
            return status
        else:
            success.append("{0} - {1}".format(contactName[index],number))
            return 'sent!'
    elif choice == "messageWithMedia":
        if status := sendMedia(index,number,hasMessage=True):
            failed.append("{0} - {1}".format(contactName[index],number))
            return status
        else:
            success.append("{0} - {1}".format(contactName[index],number))
            return 'sent!'
            
def sendMedia(index,num,hasMessage=False):
    global message,encodedMedia,mediaName
    if checkNumberStatus(num):        
        if hasMessage:
            finalMessage = message
            for i, variable in enumerate(variables):
                finalMessage = formatMessage(finalMessage,'[VAR'+str(i+1)+']',variable[index])
            request = browser.execute_script("return WPP.chat.sendFileMessage('{0}@c.us',`{1}`,{{createChat:true,caption:`{3}`,filename:`{2}`}})".format(num,encodedMedia,mediaName,finalMessage))
            
        else:
            request = browser.execute_script("return WPP.chat.sendFileMessage('{0}@c.us',`{1}`,{{createChat:true,filename:`{2}`}})".format(num,encodedMedia,mediaName))
            
            
        if json.loads(json.dumps(request))['sendMsgResult']['_value'] == "OK" :
            logFile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S - ")+num+" Message sent successfully\n")
            return False
        else:
            logFile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S - ")+num+" Big problem with sending message.\n")
            return "failed!"
    else:
        logFile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S - ")+num+" Wrong number\n")
        nonWhatsappNumbers.append(num)
        return "Don't have Whatsapp number"

def formatMessage(input, pattern, replaceWith): 
    return input.replace(pattern, replaceWith) 

def sendOnlyMessage(index,num):
    global message,hyperlink,linkTitle,linkDescription,linkImage            
    
    finalMessage = message
    for i, variable in enumerate(variables):
        finalMessage = formatMessage(finalMessage,'[VAR'+str(i+1)+']',variable[index])
    
    if checkNumberStatus(num):
        # print("checknumbercalled")
        if hyperlink == None:
            request = browser.execute_script("return WPP.chat.sendTextMessage('{0}@c.us',`{1}`,{{createChat: true, linkPreview:false}})".format(num,finalMessage),)
        else:
            request = browser.execute_script("return WPP.chat.sendTextMessage('{0}@c.us',`{1}`,{{createChat: true}})".format(num,finalMessage))
        if request:
            logFile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S - ")+num+" Message sent successfully\n")
            return False
        else:
            logFile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S - ")+num+" Big problem with sending message.\n")
            return "failed"
    else:
        logFile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S - ")+num+" Wrong number\n")
        return "Don't have Whatsapp number"

def checkNumberStatus(num):
    global message,whatsappNumbers,nonWhatsappNumbers
    # print("inside checknumberstatus")
    promis = browser.execute_script("return WPP.contact.queryExists('{0}@c.us');".format(num))
    # print(json.loads(json.dumps(promis))['status']) # 200 OR 404
    print(json.loads(json.dumps(promis))) # 200 OR 404
    if json.loads(json.dumps(promis)) != None:
        logFile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S - ")+num+" Have whatesapp\n")
        return True
    else :
        return False

def filterWhatsappNumbers(num):
    promis = browser.execute_script("return WPP.contact.queryExists('{0}@c.us');".format(num))
    
    # print(json.loads(json.dumps(promis))['status']) # 200 OR 404
    if json.loads(json.dumps(promis)) != None:
        return True
    else :
        return False

def initialiseLogFile():
    global logFile
    if not os.path.exists(f'{pathToAppData}/logs'):
        os.makedirs(f'{pathToAppData}/logs')
    logFileName = "Log-"+datetime.now().strftime("%Y%m%d%H%M%S")+".txt"
    logFile = open(Path(f'{pathToAppData}/logs')/logFileName,"a+",encoding='utf8')

def getAccounts():
    global pathToAccountData,accounts
    if not os.path.exists(pathToAccountData):
        os.makedirs(pathToAccountData)
    accounts = [d for d in os.listdir(pathToAccountData) if os.path.isdir(os.path.join(pathToAccountData, d))]
    if "Default" not in accounts:
        accounts.insert(0,"Default")
    return accounts

def deleteAccount():
    global pathToAccountData,account
    if(os.path.isdir(f'{pathToAccountData}/{account}')):
        shutil.rmtree(f'{pathToAccountData}/{account}')
    if(not os.path.exists(f'{pathToAccountData}/{account}')):
        return True
    else:
        return False

def quitBrowser():
    global browser
    try:
        checkMessageStatus()
        browser.close()
        browser.quit()
    except:
        pass

def getNextAccount():
    global accounts,account
    
    if account == accounts[-1]:
        account = accounts[0]
    else:
        account = accounts[accounts.index(account)+1]

def checkMessageStatus():
    global browser
    try:
        WebDriverWait(browser, 600).until_not(EC.presence_of_element_located((By.XPATH, '//span[@data-testid="status-time"]')))
        time.sleep(2)
        return True
    except:
        return False

def waitForInternetConnection():
    try:
        if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)):
            ssl._create_default_https_context = ssl._create_unverified_context
        response = urllib.request.urlopen('https://wa.encycode.com/whatsarc/wapi.js',timeout=10)
        with open(f'{pathToAppData}/wapi.js', "w") as f:
            f.write(response.read().decode('utf-8'))
        return True
    except Exception as e:
        print(e)
        return False