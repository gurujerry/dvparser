import requests
from bs4 import BeautifulSoup
import random
import time
import re
from gmail import email  # A local gmail.py with email variable of email text
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
''' A re-write of big list using element[x].parent.text '''
## Variables to edit:
gmaildate = "0210"  # Date of newest email
basedir = "/root/"
# Boolean to turn on testing mode
justTest = False; maxTest = 10
useProxy = True
# Compares to previous CSV to reduce page lookups
compareCSV = False; newToCSV = False; oldCSV = f'{basedir}oldfile.csv'
# Remove low ratings
filterRating = True; minRating = 4.2
outputCSV = True; newCSV = f'{basedir}{gmaildate}.csv'; filteredCSV = f'{basedir}{gmaildate}-filtered.csv'
printRows = False
sleepMin = 2; sleepMax = 5
# Old remove low ratings Regex: ^"([1-3]|(4("|\.[0-1]))).*\n

proxies = {
  "http": "http://12.69.91.226:80"
}


def parseCSV(filepath):
    with open(filepath, mode='r') as csvfile:
        reader = csv.DictReader(csvfile)
        csvList = list(reader)
    return csvList


def writeCSV(writeFile, rowList, filterRating=False):
    with open(writeFile, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        writer.writerow(['Rating', 'Beer Name', 'Price', 'Abv', 'URL', 'Style', 'Ratings'])
        if filterRating:
            for row in rowList:
                try:
                    rating = float(row[0])
                    if rating < minRating:
                        continue
                except ValueError:
                    pass
                writer.writerow(row)
        else:
            writer.writerows(fullColumnList)


#url = 'http://ifconfig.me' #Gets IP
def get_data_from_ut(url, useProxy=False):
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


def parseLink(linkDescription):
    linkDescription = linkDescription.strip('\n')
    # Is the regex end of line and group 2 below necessary/wrong?
    matchLimit = re.match(r'(.*)( - limit.*?) .*', linkDescription, re.M | re.I)  # remove ' - limit.*
    matchLeft = re.match(r'(.*)( - [0-9]+ left.*?).*', linkDescription, re.M | re.I)  # remove ' - left.*
    matchIce = re.match(r'(.*)( - .*ice.?pack.*?) .*', linkDescription, re.M | re.I)  # was picky
    if matchLimit:
        print("   Found regex Limit")
        linkDescription = matchLimit.group(1)
    if matchLeft:
        print("   Found regex Left")
        linkDescription = matchLeft.group(1)
    if matchIce:
        print("   Found regex Ice")
        linkDescription = matchIce.group(1)
    if '$' not in linkDescription:
        #linkDescription = False #TypeError: argument of type 'bool' is not iterable
        linkDescription = "Bad Link"
    if 'unsubscribe' in linkDescription.lower():
        #linkDescription = False
        linkDescription = "Bad Link"
    return linkDescription


if compareCSV or outputCSV:
    import csv

if compareCSV:
    import os.path
    if not os.path.exists(oldCSV):
        raise Exception(f'File not exist: {oldCSV}')
    oldCSVList = parseCSV(oldCSV)

# Get all email links and their parents, written this way because parent.link
#   can be duplicated and parent.string can be 3 different edge cases
html_doc = BeautifulSoup(email, 'html.parser')
allLinks = html_doc.findAll('a')  # len(allLinks) 308
allElems = len(allLinks) - 1
linkTextList = []; fullColumnList = []; newItemList = []; total = 0; beername = ""
foundInCSV = foundNAInCSV = foundPriceInCSV = webRequests = totalFilteredRows = 0
#for link in allLinks[195:315]:  #debugging
for link in allLinks:
    itemList = []; csvAddedRecord = False
    total += 1
    elem = total - 1
    print(f"Element number {elem} / {allElems}")
    #print(parseLink(link.parent.text))
    if justTest and total > maxTest:
        print("Stopping Processing")
        break
    # TODO: pass this to Function parse
    if link.parent.text in linkTextList:  # Check for dupe links?
        print(f"    Got a dupe link: {link.parent.text.strip()}")
        continue
    else:
        linkTextList.append(link.parent.text,)
        #print(link.parent.text)
    checkGoodLink = parseLink(link.parent.text)
    if checkGoodLink == "Bad Link":
        print("     Bad Link, skipping")
        continue
    # Spaces optional (?) because DV sucks at formatting
    beerEmailDescription = re.match(r'(.*)( ?- ?)(.*)', checkGoodLink, re.M | re.I)
    beername = beerEmailDescription.group(1)
    formatBeername = beername.strip()
    price = beerEmailDescription.group(3)
    formatPrice = price.strip()
    if compareCSV:
        #NameList = [row["Beer Name"] for row in oldCSVList]
        # Each Element in oldCSVList[] is an OrderedDict
        for elem in oldCSVList:
            if elem.get('Beer Name') == formatBeername:
                print(f'   Name match {formatBeername}')
                foundInCSV += 1
                csvRating = elem.get('Rating')
                if csvRating == 'N/A':
                    foundNAInCSV += 1
                    print(f'        No CSV rating, looking up')
                    continue
                csvName = elem.get('Beer Name')
                csvPrice = elem.get('Price')
                csvABV = elem.get('Abv')
                csvURL = elem.get('URL')
                csvStyle = elem.get('Style')
                csvRatings = elem.get('Ratings')
                if formatPrice == csvPrice:
                    foundPriceInCSV += 1
                    itemList = [csvRating, csvName, csvPrice, csvABV, csvURL, csvStyle, csvRatings]
                else:
                    print(f'        Price difference email: {formatPrice} csv: {csvPrice}')
                    itemList = [csvRating, csvName, formatPrice, csvABV, csvURL, csvStyle, csvRatings]
                fullColumnList.append(itemList)
                csvAddedRecord = True
        if csvAddedRecord:  # TODO: probably a better way continue an outer nested for loop
            continue
            #for key, value in elem.items():
            #    print(f'key: {key} value: {value}')
    time.sleep(random.uniform(sleepMin, sleepMax))  # Throttle requests, uniform vs randint for floating numbers
    #resp = get_data_from_ut(link['href'])  # not itemList[0]
    if useProxy:
        resp = get_data_from_ut(link['href'], useProxy=True)
    else:
        resp = get_data_from_ut(link['href'])
    webRequests += 1
    #? Replace with resp.raise_for_status()
    if resp.status_code != 200:
        print("No 200 error")
        break
    resp_doc = BeautifulSoup(resp.text, 'html.parser')
    rating = resp_doc.find("span", {"class": "num"}).text  # '(4.67)'
    formatRating = rating.strip('()')
    abv = resp_doc.find("p", {"class": "abv"}).text
    formatAbv = abv.strip('\nABV ')
    raters = resp_doc.find("p", {"class": "raters"}).text
    formatRaters = raters.strip('\nRatings ')
    style = resp_doc.find("p", {"class": "style"}).text
    # Put CSV: Rating, Name, Price, Abv, URL, Style, Ratings Count
    itemList = [formatRating, formatBeername, formatPrice, formatAbv, resp.url, style, formatRaters]
    if newToCSV:
        newItemList.append(itemList)
    print(f'   New: Name: {formatBeername} Rating: {formatRating}')
    fullColumnList.append(itemList)


def printList(columnList):
    filteredRows = 0
    print('"Rating","Beer Name","Price","Abv","URL","Style","Ratings"')
    for c in columnList:
        if filterRating:
            #print(f"Testing {c[0]}")
            try:
                rating = float(c[0])
                if rating < minRating:
                    filteredRows += 1
                    continue
            except ValueError:
                pass
                #print(f"    Can't convert to float {c[0]}")
            # I hated the ugly regex below and replaced with float comparison above
            #if re.match( r'^([0-3]|(4($|\.[0-1]))).*$', c[0] ):
        print(f'"{c[0]}","{c[1]}","{c[2]}","{c[3]}","{c[4]}","{c[5]}","{c[6]}"')
    return filteredRows


if printRows:
    totalFilteredRows = printList(fullColumnList) # Full list
    print("NEW BEER LIST:")
    filterRating = False
    newFilteredRows = printList(newItemList) # Should be 0 because of above set to False

if outputCSV:
    writeCSV(newCSV, fullColumnList)
    if filterRating:
        writeCSV(filteredCSV, fullColumnList, filterRating=True)

print(f'Total: Rows: {len(fullColumnList)} Filtered: {totalFilteredRows} Web Calls: {webRequests}')
print(f'   Found in Previous CSV: Name: {foundInCSV} Price: {foundPriceInCSV} N/A Rating: {foundNAInCSV}')
print(f'   New To CSV: {len(newItemList)} Filtered: {newFilteredRows}')
