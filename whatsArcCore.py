from selenium import webdriver
from selenium.common.exceptions import JavascriptException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from linkpreview import Link, LinkPreview, LinkGrabber
import requests
from requests import get
import shutil

from pathlib import Path

from datetime import datetime
import time
import os
import argparse
import pandas as pd
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
pathToAccountData = os.getenv('LOCALAPPDATA')+'\\whatsArc\\Accounts'
pathToAppData = os.getenv('LOCALAPPDATA')+'\\whatsArc'
account = "Default"
accounts = []
isRotate = False
rotateInterval = 100

parser = argparse.ArgumentParser(description='PyWhatsapp Guide')
parser.add_argument('--chrome_driver_path', action='store', type=str, default='./chromedriver.exe',help='chromedriver executable path (MAC and Windows path would be different)')
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

def importContacts(csvPath):
    print(csvPath)
    global contactNumber, contactName, variables

    # Create a dataframe from
    # colnames = ['name', 'mobile','VAR1','VAR2','VAR3','VAR4','VAR5']
    data = pd.read_csv(csvPath).fillna("")
    print(data)

    # Clear lists
    contactName = contactNumber = variables = []
    
    contactName = data.name.tolist()
    # contactName.pop(0)
    contactNumber = list(map(str,data.mobile.tolist()))
    # contactNumber.pop(0)
    variables.append(data.VAR1.tolist())
    variables.append(data.VAR2.tolist())
    variables.append(data.VAR3.tolist())
    variables.append(data.VAR4.tolist())
    variables.append(data.VAR5.tolist())

def whatsappLogin(chrome_path=args.chrome_driver_path):
    global wait, browser, whatsappLink,account
    chrome_options = Options()
    chrome_options.add_argument('--user-data-dir='+pathToAccountData+'\\'+account)
    chrome_options.set_capability('unhandledPromptBehavior', 'accept')
    # chrome_options.add_argument('headless')
    browser = webdriver.Chrome(executable_path=chrome_path, options=chrome_options)
    wait = WebDriverWait(browser, 600)
    browser.get(whatsappLink)
    browser.set_window_position(0, 0)
    browser.set_window_size(500, 500)
    # browser.maximize_window()
    print("QR scanned")    
    try:
        WebDriverWait(browser, 600).until(EC.presence_of_element_located((By.XPATH, '//div[@data-asset-intro-image="true" or @data-asset-intro-image-light="true" or @data-asset-intro-image-dark="true"]')))
        with open("wapi.js",'r') as script:
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
        if sendOnlyMessage(index,number):
            success.append("{0} - {1}".format(contactName[index],number))
        else:
            failed.append("{0} - {1}".format(contactName[index],number))
    elif choice == "onlyMedia":
        if sendMedia(index,number):
            success.append("{0} - {1}".format(contactName[index],number))
        else:
            failed.append("{0} - {1}".format(contactName[index],number))
    elif choice == "document":
        if sendMedia(index,number):
            success.append("{0} - {1}".format(contactName[index],number))
        else:
            failed.append("{0} - {1}".format(contactName[index],number))
    elif choice == "messageWithMedia":
        if sendMedia(index,number,hasMessage=True):
            success.append("{0} - {1}".format(contactName[index],number))
        else:
            failed.append("{0} - {1}".format(contactName[index],number))
            
def sendMedia(index,num,hasMessage=False):
    global message,encodedMedia,mediaName
    if checkNumberStatus(num):        
        if hasMessage:
            finalMessage = message
            for i, variable in enumerate(variables):
                finalMessage = formatMessage(finalMessage,'[VAR'+str(i+1)+']',variable[index])
            # print(encodedMedia)
            # print("window.WAPI.sendImage(`{0}`,'{1}@c.us',`{2}`,`{3}`)".format(encodedMedia,num,mediaName,message))
            request = browser.execute_script("return window.WAPI.sendImage(`{0}`,'{1}@c.us',`{2}`,`{3}`)".format(encodedMedia,num,mediaName,finalMessage))
        else:
            request = browser.execute_script("return window.WAPI.sendImage(`{0}`,'{1}@c.us',`{2}`)".format(encodedMedia,num,mediaName))

        if request == None :
            logFile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S - ")+num+" Message sent successfully\n")
            return True
        else:
            logFile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S - ")+num+" Big problem with sending message.\n")
            return False
    else:
        logFile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S - ")+num+" Wrong number\n")
        nonWhatsappNumbers.append(num)
        return False

def getImagefromUrl():
    global linkImage
    try:
        filename = linkImage.split("/")[-1]
        r = requests.get(linkImage, stream = True)
        time.sleep(5)
        if r.status_code == 200:
            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
            r.raw.decode_content = True
            with open(filename,'wb') as f:
                shutil.copyfileobj(r.raw, f)
            encodeMedia(filename,True)
            if os.path.exists(filename):
                os.remove(filename)
    except:
        linkImage = ""
    else:
        print('Image Couldn\'t be retreived')

def getLinkPreviewData():
    global linkTitle,linkDescription,linkImage,hyperlink
    grabber = LinkGrabber(
        initial_timeout=10, maxsize=1048576, receive_timeout=5, chunk_size=1024,
    )

    content = grabber.get_content(hyperlink)
    link = Link(hyperlink, content)

    preview = LinkPreview(link, parser="lxml")

    linkTitle = linkDescription = linkImage = ""

    if preview.title != None:
        linkTitle = preview.title        
    if preview.description != None:
        linkDescription = linkDescription
    if preview.image != None:
        linkImage = preview.image
        getImagefromUrl()

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
            request = browser.execute_script("return window.WAPI.sendMessage('{0}@c.us',`{1}`)".format(num,finalMessage))
        else:
            request = browser.execute_script("return window.WAPI.sendMessageWithThumb(`{0}`,`{1}`,`{2}`,`{3}`,`{4}`,'{5}@c.us')".format(linkImage,hyperlink,linkTitle,linkDescription,message,num))
        if request:
            logFile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S - ")+num+" Message sent successfully\n")
            return True
        else:
            logFile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S - ")+num+" Big problem with sending message.\n")
            return False
    else:
        logFile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S - ")+num+" Wrong number\n")
        return False

def checkNumberStatus(num):
    global message,whatsappNumbers,nonWhatsappNumbers
    # print("inside checknumberstatus")
    promis = browser.execute_script("return window.Store.WapQuery.queryExist('{0}@c.us');".format(num))
    print(json.loads(json.dumps(promis))['status']) # 200 OR 404
    if json.loads(json.dumps(promis))['status'] == 200:
        logFile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S - ")+num+" Have whatesapp\n")
        while True:
            try:
                browser.execute_script("return window.WAPI.getChat('{0}@c.us')".format(num))
            except JavascriptException as e:
                if "sendMessage" in str(e):
                    browser.execute_script("return openChat('{0}');".format(num))
                    time.sleep(3)
                    logFile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S - ")+num+" New Contact Number\n")
                    break
                else:
                    logFile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S - ")+num+" "+str(e)+"\n")
                    return False
                continue
            break

        return True
    if json.loads(json.dumps(promis))['status'] == 404:
        logFile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S - ")+num+" dosen't have whatesapp\n")
        return False
    else :
        logFile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S - ")+num+" another ERROR\n")
        return False

def filterWhatsappNumbers(num):
    promis = browser.execute_script("return window.Store.WapQuery.queryExist('{0}@c.us');".format(num))
    # print(json.loads(json.dumps(promis))['status']) # 200 OR 404
    if json.loads(json.dumps(promis))['status'] == 200:
        return True
    if json.loads(json.dumps(promis))['status'] == 404:
        return False
    else :
        return False

def initialiseLogFile():
    global logFile
    if not os.path.exists(pathToAppData+"\\logs"):
        os.makedirs(pathToAppData+"\\logs")
    logFileName = "Log-"+datetime.now().strftime("%Y%m%d%H%M%S")+".txt"
    logFile = open(Path(pathToAppData+'\\logs')/logFileName,"a+",encoding='utf8')

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
    if(os.path.isdir(pathToAccountData+'\\'+account)):
        shutil.rmtree(pathToAccountData+'\\'+account)
    if(not os.path.exists(pathToAccountData+'\\'+account)):
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
        response = urllib.request.urlopen('https://wa.encycode.com/whatsarc/wapi.js',timeout=5)
        with open("wapi.js", "w") as f:
            f.write(response.read().decode('utf-8'))
        return True
    except Exception as e:
        print(e)
        return False