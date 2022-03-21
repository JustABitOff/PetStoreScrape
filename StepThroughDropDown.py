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


def StepThroughDropDown(url):
    driver = webdriver.Chrome(ChromeDriverManager().install())

    #driver.get("https://www.petsmart.com/dog/food/dry-food/purina-pro-plan-focus-adult-dry-dog-food---sensitive-skin-and-stomach-salmon-and-rice-36648.html")
    driver.get("https://www.petsmart.com/dog/food/simply-nourish-shreds-adult-wet-dog-food---natural-52741.html")

    tempSoup = BeautifulSoup(driver.page_source, 'lxml')
    selectDiv = tempSoup.find('div', {'class': 'variant-select'})
    selects = selectDiv.findChild('select')['class']
    dropdownType = selects[0]

    drop = Select(wait(driver, 15).until(EC.presence_of_element_located((By.ID, dropdownType))))
    options = drop.options

    for option in options:
        
        drop.select_by_visible_text(option.text)
        time.sleep(1)
        page_source = driver.page_source

        soup = BeautifulSoup(page_source, 'lxml')

        productNameElem = soup.find('h1', {'class': 'pdp-product-name'})
        if productNameElem:
            for child in productNameElem.find_all():
                child.decompose()
            productName = productNameElem.text.strip()
        else:
            productName = None

        basePriceElem = soup.find('span', {'class': 'product-price-standard'})
        if basePriceElem:
            for child in basePriceElem.find_all('span'):
                child.decompose()
            basePrice = basePriceElem.text.strip()
            basePrice = float(basePrice[1::])
        else:
            basePrice = None

        discountedPriceElem = soup.find('span', {'class': 'product-price-sales'})
        if discountedPriceElem:
            for child in discountedPriceElem.find_all():
                child.decompose()
            discountedPrice = discountedPriceElem.text.strip()
            discountedPrice = float(discountedPrice[1::])
        else:
            discountedPrice = None

        brandElem = soup.find('a', {'class': 'brand-details'})
        if brandElem:
            for child in brandElem.find_all():
                child.decompose()
            brand = brandElem.text.strip()
        else:
            brand = None

        productIdElem = soup.find('span', itemprop='productID')
        if productIdElem:
            for child in productIdElem.find_all():
                child.decompose()
            productID = productIdElem.text.strip()
        else:
            productID = None

        stockStatusElem = soup.find('div', {'class': 'pdp-sth-outofstock'})
        if stockStatusElem:
            isProductOutOfStock = True
        else:
            isProductOutOfStock = False

        if dropdownType == 'size':
            flavorElem = soup.find('div', {'id': 'customFlavor'})
            if flavorElem:
                for child in flavorElem.find_all('strong'):
                    flavor = child.text.strip()
            else:
                flavor = None

            size = option.text.strip()
        
        elif dropdownType == 'customFlavor':
            flavor = option.text.strip()

            sizeElem = soup.find('div', {'id': 'size'})
            if sizeElem:
                for child in sizeElem.find_all('strong'):
                    size = child.text.strip()
            else:
                size = None    
        else:
            flavor = '--Who Knows?--'
            size = '--Who Knows?--'

        productDocument = {
            'Product ID': productID,
            'Brand': brand,
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

        print(productDocument)
        print('\n')

        time.sleep(randint(0, 3))


#TODO:
##From main search page, a class='name-link' contains the href to go to a specific product page
##Break