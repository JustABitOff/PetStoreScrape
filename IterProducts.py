from random import randint
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
from math import ceil
import re
from multiprocessing import Pool
import tqdm
from dotenv import load_dotenv
import os
from pymongo import MongoClient

def GetNumberOfPages(soup: BeautifulSoup, step: int):
    resultsHitsDiv = soup.find('div', {'class': 'results-hits'}).text
    numProducts = re.sub(r'\D+', '', resultsHitsDiv).strip()
    numProducts = int(numProducts) - 1
    numPages = ceil(numProducts / step)

    return numPages

def GetProductURLs(numPages: int, step: int, baseURL: str, driver):
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

    return productURLs

def GetProductName(soup: BeautifulSoup):
    productNameElem = soup.find('h1', {'class': 'pdp-product-name'})
    if productNameElem:
        for child in productNameElem.find_all():
            child.decompose()
        productName = productNameElem.text.strip()
    else:
        productName = None
    
    return productName

def GetProductID(soup: BeautifulSoup):
    productIdElem = soup.find('span', itemprop='productID')
    if productIdElem:
        for child in productIdElem.find_all():
            child.decompose()
        productID = productIdElem.text.strip()
    else:
        productID = None
    
    return productID

def GetBrand(soup: BeautifulSoup):
    brandElem = soup.find('a', {'class': 'brand-details'})
    if brandElem:
        for child in brandElem.find_all():
            child.decompose()
        brand = brandElem.text.strip()
    else:
        brand = None

    return brand

def GetBasePrice(soup: BeautifulSoup):
    basePriceElem = soup.find('span', {'class': 'product-price-standard'})
    if basePriceElem:
        for child in basePriceElem.find_all('span'):
            child.decompose()
        basePrice = basePriceElem.text.strip()
        basePrice = float(basePrice[1::])
    else:
        basePrice = None

    return basePrice

def GetDiscountedPrice(soup: BeautifulSoup):
    discountedPriceElem = soup.find('span', {'class': 'product-price-sales'})
    if discountedPriceElem:
        for child in discountedPriceElem.find_all():
            child.decompose()
        discountedPrice = discountedPriceElem.text.strip()
        discountedPrice = float(discountedPrice[1::])
    else:
        discountedPrice = None

    return discountedPrice

def GetSize(soup: BeautifulSoup):
    sizeElem = soup.find('div', {'id': 'size'})
    if sizeElem:
        for child in sizeElem.find_all('strong'):
            size = child.text.strip()
    else:
        size = None  
    
    return size

def GetFlavor(soup: BeautifulSoup):
    flavorElem = soup.find('div', {'id': 'customFlavor'})
    if flavorElem:
        for child in flavorElem.find_all('strong'):
            flavor = child.text.strip()
    else:
        flavor = None
    
    return flavor

def GetOutOfStockStatus(soup: BeautifulSoup):
    stockStatusElem = soup.find('div', {'class': 'pdp-sth-outofstock'})
    if stockStatusElem:
        isProductOutOfStock = True
    else:
        isProductOutOfStock = False

    return isProductOutOfStock

def GetProductDocument(url: str):
    opts = webdriver.ChromeOptions()
    opts.add_argument('--headless')
    prefs = {"profile.managed_default_content_settings.images":2,
             "profile.default_content_setting_values.notifications":2,
             "profile.managed_default_content_settings.stylesheets":2,
             "profile.managed_default_content_settings.cookies":2,
             "profile.managed_default_content_settings.javascript":1,
             "profile.managed_default_content_settings.plugins":1,
             "profile.managed_default_content_settings.popups":2,
             "profile.managed_default_content_settings.geolocation":2,
             "profile.managed_default_content_settings.media_stream":2,
    }
    opts.add_experimental_option("prefs",prefs)
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=opts)
    driver.get(url)
    wait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'search-result-content')))

    soup = BeautifulSoup(driver.page_source, 'lxml')
    selectDiv = soup.find('div', {'class': 'variant-select'})
    documents = []
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
                'ProductID': productID,
                'Brand': brand,
                'ProductName': productName,
                'BasePrice': {
                    'Amount': basePrice,
                    'Currency': 'USD'
                },
                'DiscountedPrice': {
                    'Amount': discountedPrice,
                    'Currency': 'USD'
                },
                'Size': size,
                'Flavor': flavor,
                'IsProductOutOfStock': isProductOutOfStock,
                'CreatedDatetime': datetime.now().isoformat()
            }

            documents.append(productDocument)

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
            'ProductID': productID,
            'Brand': brand,
            'ProductName': productName,
            'BasePrice': {
                'Amount': basePrice,
                'Currency': 'USD'
            },
            'DiscountedPrice': {
                'Amount': discountedPrice,
                'Currency': 'USD'
            },
            'Size': size,
            'Flavor': flavor,
            'IsProductOutOfStock': isProductOutOfStock,
            'CreatedDatetime': datetime.now().isoformat()
        }

        documents.append(productDocument)

        time.sleep(randint(0, 3))
        
    driver.close()

    return documents

def getMongoCollection(uri: str, db: str, collection: str):
    """
    Returns a MongoDB collection object for a give Database and Collection.\n
    Keyword Arguments:\n    
    uri -- MongoDB URI Connection String \n
    db -- Name of the MongoDB Database (type) \n
    collection -- Name of the MongoDB Collection
    """

    client = MongoClient(uri)
    dbase = client[db]
    collObj = dbase[collection]

    return collObj

###############################################################################################
def main():
    baseURL = "https://www.petsmart.com/dog/food"
    step = 36

    opts = webdriver.ChromeOptions()
    opts.add_argument('--headless')
    prefs = {"profile.managed_default_content_settings.images":2,
             "profile.default_content_setting_values.notifications":2,
             "profile.managed_default_content_settings.stylesheets":2,
             "profile.managed_default_content_settings.cookies":2,
             "profile.managed_default_content_settings.javascript":1,
             "profile.managed_default_content_settings.plugins":1,
             "profile.managed_default_content_settings.popups":2,
             "profile.managed_default_content_settings.geolocation":2,
             "profile.managed_default_content_settings.media_stream":2,
    }
    opts.add_experimental_option("prefs",prefs)
    serv = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=serv, options=opts)
    driver.get(baseURL)
    wait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'results-hits')))
    soup = BeautifulSoup(driver.page_source, 'lxml')

    numPages = GetNumberOfPages(soup, step)
    productURLs = GetProductURLs(numPages, step, baseURL, driver)
    driver.close()

    with Pool(processes=4) as pool, tqdm.tqdm(total=len(productURLs)) as progBar:
        documents = []
        for url in pool.imap_unordered(GetProductDocument, productURLs):
            documents.extend(url)
            progBar.update()

    ###hmm...Maybe move to a function
    load_dotenv()
    MONGO_USERNAME = os.getenv("MONGO_USERNAME")
    MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
    MONGO_PORT = os.getenv("MONGO_PORT")

    mongoURI = 'mongodb+srv://{}:{}@prodcluster.{}.mongodb.net/'.format(MONGO_USERNAME, MONGO_PASSWORD, MONGO_PORT)
    db = 'PetStore'
    collection = 'DogFood'

    DogFoodColl = getMongoCollection(mongoURI, db, collection)

    #need to start adding in the MongoDB logic here.
    DogFoodColl.insert_many(
        documents
    )


if __name__ == "__main__":
    main()

#TODO:
##Add documents to MongoDB if they don't exist
##If they do exist, update them with the following logic
    ##Move the existing Base Price to a list within the main document. 
    ##Also move the AsOfDatetime witht he Base Price
    ##Finally, upsert the NEW Base Price into the document, update the discounted price, update all other potentially changing fields
    ##Or should I just insert a new document? Hmmmm.
        ##Maybe this because there is a ProductID. I could use this to track all things related to each product. 1 product -> Many documents