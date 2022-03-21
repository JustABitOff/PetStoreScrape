from random import randint
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
from math import ceil
import re

def GetNumberOfPages(soup, step):
    resultsHitsDiv = soup.find('div', {'class': 'results-hits'}).text
    numProducts = re.sub(r'\D+', '', resultsHitsDiv).strip()
    numProducts = int(numProducts) - 1
    numPages = ceil(numProducts / step)

    return numPages

def GetProductName(soup):
    productNameElem = soup.find('h1', {'class': 'pdp-product-name'})
    if productNameElem:
        for child in productNameElem.find_all():
            child.decompose()
        productName = productNameElem.text.strip()
    else:
        productName = None
    
    return productName

def GetProductID(soup):
    productIdElem = soup.find('span', itemprop='productID')
    if productIdElem:
        for child in productIdElem.find_all():
            child.decompose()
        productID = productIdElem.text.strip()
    else:
        productID = None
    
    return productID

def GetBrand(soup):
    brandElem = soup.find('a', {'class': 'brand-details'})
    if brandElem:
        for child in brandElem.find_all():
            child.decompose()
        brand = brandElem.text.strip()
    else:
        brand = None

    return brand

def GetBasePrice(soup):
    basePriceElem = soup.find('span', {'class': 'product-price-standard'})
    if basePriceElem:
        for child in basePriceElem.find_all('span'):
            child.decompose()
        basePrice = basePriceElem.text.strip()
        basePrice = float(basePrice[1::])
    else:
        basePrice = None

    return basePrice

def GetDiscountedPrice(soup):
    discountedPriceElem = soup.find('span', {'class': 'product-price-sales'})
    if discountedPriceElem:
        for child in discountedPriceElem.find_all():
            child.decompose()
        discountedPrice = discountedPriceElem.text.strip()
        discountedPrice = float(discountedPrice[1::])
    else:
        discountedPrice = None

    return discountedPrice

def GetSize(soup):
    sizeElem = soup.find('div', {'id': 'size'})
    if sizeElem:
        for child in sizeElem.find_all('strong'):
            size = child.text.strip()
    else:
        size = None  
    
    return size

def GetFlavor(soup):
    flavorElem = soup.find('div', {'id': 'customFlavor'})
    if flavorElem:
        for child in flavorElem.find_all('strong'):
            flavor = child.text.strip()
    else:
        flavor = None
    
    return flavor

def GetOutOfStockStatus(soup):
    stockStatusElem = soup.find('div', {'class': 'pdp-sth-outofstock'})
    if stockStatusElem:
        isProductOutOfStock = True
    else:
        isProductOutOfStock = False

    return isProductOutOfStock

def GetProductDocument(url):
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(url)

    soup = BeautifulSoup(driver.page_source, 'lxml')
    selectDiv = soup.find('div', {'class': 'variant-select'})
    if selectDiv:
        selects = selectDiv.findChild('select')['class']
        dropdownType = selects[0]

        drop = Select(wait(driver, 15).until(EC.presence_of_element_located((By.ID, dropdownType))))
        options = drop.options

        for option in options:
            
            drop.select_by_visible_text(option.text)
            time.sleep(1)
            page_source = driver.page_source

            soup = BeautifulSoup(page_source, 'lxml')
            productID = GetProductID(soup)
            brand = GetBrand(soup)
            productName = GetProductName(soup)
            basePrice = GetBasePrice(soup)
            discountedPrice = GetDiscountedPrice(soup)

            if dropdownType == 'size':
                size = option.text.strip()
                flavor = GetFlavor(soup)
            elif dropdownType == 'customFlavor':
                size = GetSize(soup)
                flavor = option.text.strip()
            else:
                flavor = '--Who Knows--'
                size = '--Who Knows--'

            isProductOutOfStock = GetOutOfStockStatus(soup)

            productDocument = {
                'Product ID': productID,
                'Brand': brand,
                'Product Name': productName,
                'Base Price': {
                    'Amount': basePrice,
                    'Currency': 'USD'
                },
                'Discounted Price': {
                    'Amount': discountedPrice,
                    'Currency': 'USD'
                },
                'Size': size,
                'Flavor': flavor,
                'Is Product Out of Stock': isProductOutOfStock,
                'Inserted Datetime': datetime.now().isoformat()
            }

            time.sleep(randint(0, 3))

    else:
        soup = BeautifulSoup(driver.page_source, 'lxml')
        productID = GetProductID(soup)
        brand = GetBrand(soup)
        productName = GetProductName(soup)
        basePrice = GetBasePrice(soup)
        discountedPrice = GetDiscountedPrice(soup)
        size = GetSize(soup)
        flavor = GetFlavor(soup)
        isProductOutOfStock = GetOutOfStockStatus(soup)

        productDocument = {
            'Product ID': productID,
            'Brand': brand,
            'Product Name': productName,
            'Base Price': {
                'Amount': basePrice,
                'Currency': 'USD'
            },
            'Discounted Price': {
                'Amount': discountedPrice,
                'Currency': 'USD'
            },
            'Size': size,
            'Flavor': flavor,
            'Is Product Out of Stock': isProductOutOfStock,
            'Inserted Datetime': datetime.now().isoformat()
        }

        time.sleep(randint(0, 3))

    return productDocument

###############################################################################################
def main():
    baseURL = "https://www.petsmart.com/dog/food"
    start = 0
    step = 36

    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(baseURL)
    wait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'results-hits')))
    soup = BeautifulSoup(driver.page_source, 'lxml')

    numPages = GetNumberOfPages(soup, step)
    productURLs = []
    for page in range(numPages):
        start = step * page
        driver.get("{}/?start={}&sz={}".format(baseURL, start, step))
        soup = BeautifulSoup(driver.page_source, 'lxml')
        wait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'search-result-content')))

        li = soup.find_all('li', {'class': 'grid-tile gtm-grid-tile col-md-4 col-sm-12'})

        for i in li:
            productPath = i.find('a', {'class': 'name-link'})['href']
            productURL = "{}{}".format(baseURL, productPath)
            productURLs.append(productURL)
        
        time.sleep(randint(0, 3))

    documents = []
    for url in productURLs:
        documents.append(GetProductDocument(url))

    for i in documents:
        print(i)

if __name__ == "__main__":
    main()