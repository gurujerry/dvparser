import requests
from bs4 import BeautifulSoup
import random
import time
import re
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
''' A re-write of big list using element[x].parent.text '''
## Variables to edit:
#Boolean to turn on testing mode
justTest = False ; maxTest = 10
useProxy = True
#Compares to previous CSV to reduce page lookups
compareCSV = False ; oldCSV = '/path/to/oldfile.csv'
 #Remove low ratings
filterRating = True ; minRating = 4.2
sleepMin = 2; sleepMax = 5  #1,2
#Old Regex to remove low ratings: ^"(3.*|4\.[0-1].*)\n  OR Better: ^"([1-3]|(4("|\.[0-1]))).*\n

proxies = {
  "http": "http://12.69.91.226:80"
}

def parseCSV(filepath):
    with open(filepath, mode='r') as csvfile:
        reader = csv.DictReader(csvfile)
        csvList = list(reader)
    return csvList


#url = 'http://ifconfig.me' #Gets IP
def get_data_from_ut(url, useProxy = False):
    try:
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0'
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'
        headers = {'User-Agent': user_agent}
        # Make web request and don't verify SSL/TLS certs
        if useProxy:
            response = requests.get(url, headers=headers, verify=False, proxies=proxies)
        else:
            response = requests.get(url, headers=headers, verify=False)
        #return response.text
        return response
    except Exception as e:
        print('[!]   ERROR - Untappd issue: {}'.format(str(e)))
        exit(1)


## Get all the email links and their parents
html_doc = BeautifulSoup(gmail, 'html.parser')
allLinks = html_doc.findAll('a') #len(allLinks) 308
## TEST written this way because parent.link can be duplicated and parent.string can be 3 different edge cases
def parseLink(linkDescription):
    linkDescription = linkDescription.strip('\n')
    ## Is the regex end of line and group 2 below necessary/wrong?
    matchLimit = re.match( r'(.*)( - limit.*?) .*', linkDescription, re.M|re.I) #remove ' - limit.*
    matchIce = re.match( r'(.*)( - .*ice.?pack.*?) .*', linkDescription, re.M|re.I) #was picky
    if matchLimit:
        print("Found regex")
        linkDescription = matchLimit.group(1)
    if matchIce:
        print("Found regex")
        linkDescription = matchIce.group(1)
    if '$' not in linkDescription:
        #linkDescription = False #TypeError: argument of type 'bool' is not iterable
        linkDescription = "Bad Link"
    if 'unsubscribe' in linkDescription.lower():
        #linkDescription = False
        linkDescription = "Bad Link"
    return linkDescription


allElems = len(allLinks) - 1
linkTextList = []; columnList = []; total = 0; beername = ""
#for link in allLinks[195:315]:  #debugging
for link in allLinks:
    itemList = []
    total += 1
    elem = total - 1
    print(f"Element number {elem} / {allElems}")
    #print(parseLink(link.parent.text))
    if justTest and total > maxTest:
        print("Stopping Processing")
        break
    ## TODO: pass this to Function parse
    if link.parent.text in linkTextList: #Check for dupe links?
        print(f"     Got a dupe link {link.parent.text}")
        continue
    else:
        linkTextList.append(link.parent.text,)
        #print(link.parent.text)
    checkGoodLink = parseLink(link.parent.text)
    if checkGoodLink == "Bad Link":
        print("Bad Link, skipping")
        continue
    # Making spaces optional (?) because DV sucks at formatting
    beerEmailDescription = re.match( r'(.*)( ?- ?)(.*)', checkGoodLink, re.M|re.I)
    beername = beerEmailDescription.group(1)
    formattedBeername = beername.strip()
    price = beerEmailDescription.group(3)
    if compareCSV:
        import csv #Move this to beginning if we ever output as CSV
        oldCSVList = parseCSV(oldCSV)
        #NameList = [row["Beer Name"] for row in oldCSVList]
        # Each Element in oldCSVList[] is an OrderedDict 
        for elem in oldCSVList:
            if elem.get('Beer Name') == formattedBeername:
                # TODO: Do stuff here like return CSV values and skip Web lookup 
                pass
            #for key, value in elem.items():
            #    print(f'key: {key} value: {value}')
    time.sleep(random.uniform(sleepMin, sleepMax)) ## Throttle between requests, uniform vs randint for floating numbers
    #resp = get_data_from_ut(link['href'])  # not itemList[0]
    if useProxy:
        resp = get_data_from_ut(link['href'], useProxy = True)
    else:
        resp = get_data_from_ut(link['href'])
    #? Replace with resp.raise_for_status()
    if resp.status_code != 200:
        print("No 200 error")
        break
    resp_doc = BeautifulSoup(resp.text, 'html.parser')
    rating = resp_doc.find("span", {"class": "num"}).text #'(4.67)'
    formattedRating = rating.strip('()')
    abv = resp_doc.find("p", {"class": "abv"}).text
    formattedAbv = abv.strip('\nABV ')
    raters = resp_doc.find("p", {"class": "raters"}).text
    formattedRaters = raters.strip('\nRatings ')
    style = resp_doc.find("p", {"class": "style"}).text
    # Put CSV: Rating, Name, Price, Abv, URL
    itemList.append([formattedRating, formattedBeername, price, formattedAbv, resp.url, style, formattedRaters])
    columnList.append(itemList)

# Print to screen Excel Friendly "0","1". TODO: Add CSV file output (docker challenges)
totalNewCSVRows = 0
for columns in columnList:
    if filterRating:
        #print(f"Testing {columns[0]}")
        try:
            rating = float(columns[0][0])
            if rating < minRating:
                #print("      Basic AF")
                continue
        except ValueError:
            pass
            #print(f"    Can't convert to float {columns[0][0]}")
        ## I hated the ugly regex below and replaced with float comparrison above
        #if re.match( r'^([0-3]|(4($|\.[0-1]))).*$', columns[0][0] ):
        #    continue
    if totalNewCSVRows == 0:
        print('"Rating","Beer Name","Price","Abv","URL","Style","Ratings"')
    c = columns[0]
    print(f'"{c[0]}","{c[1]}","{c[2]}","{c[3]}","{c[4]}","{c[5]}","{c[6]}"')
    totalNewCSVRows += 1
