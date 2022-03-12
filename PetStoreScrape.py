from enum import auto
from numpy import diff
from pymongo import MongoClient
from requests_html import HTMLSession
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
import os

# session = HTMLSession()
url = 'https://www.petsmart.com/dog/food/?start=0&sz=36'

# resp = session.get(url)
# resp.html.render()

resp = requests.get(url).text

soup = BeautifulSoup(resp, "html.parser")
div = soup.find('div', {'class': 'search-result-content'})
ul = div.find('ul')
children = ul.findChildren('li', recursive=False)

y = 1

for child in children:
    title = child.find('div', {'class': 'product-name'})
    title = title.text.replace('\n', ' ')
    print(y, title)

    numFlavorsOrSizes = child.find('div', {'class': 'product-flavour-text'})
    if numFlavorsOrSizes:
        numFlavorsOrSizes = numFlavorsOrSizes.text.replace('\n', ' ')
        print(y, numFlavorsOrSizes)
    else:
        print(y, '{} has no numFlavorsOrSizes'.format(title))


    regPrice = child.find('span', {'class': 'price-regular'})
    if regPrice:
        for i in regPrice.find_all('span'):
            i.decompose()
        regPrice  = regPrice.text.replace('\n', ' ')
        print(y, regPrice)
    else:
        print(y, '{} has no regPrice'.format(title))

    autoShipDiscount = child.find('div', {'class': 'price-text'})
    if autoShipDiscount:
        autoShipDiscount = autoShipDiscount.text.replace('\n', ' ')
        print(y, autoShipDiscount)
    else:
        print(y, '{} has no autoShipDiscount'.format(autoShipDiscount))


    autoShipPrice = child.find('div', {'class': 'price-sales tile-autoship'})
    if autoShipPrice:
        for i in autoShipPrice.find_all('div'):
            i.decompose()
        autoShipPrice = autoShipPrice.text.replace('\n', ' ')
        print(y, autoShipPrice)
    else:
        print(y, '{} has no autoShipPrice'.format(autoShipPrice))

    
    rating = child.find('div', {'class': 'rated-stars-container'})
    ratingList = []
    if rating:
        for i in rating:
            ratingList.append(i)
    else:
        pass


    print('\n')
    y += 1
# print(children[0])