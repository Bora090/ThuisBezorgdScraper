from asyncio import run
from DBMake import DBConnection, TableTypes
from time import time
import requests

maxRequests = 125

def getAt(list, index, default=None):
    try:
        return list[index]
    except IndexError:
        return default

async def getProducts():
    connection = DBConnection()
    start = time()

    if not connection.databaseExists():
        connection.makeDatabase()
    
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36", "x-country-code": "nl"}
    
    for i, (_, restaurant) in enumerate(requests.get("https://cw-api.takeaway.com/api/v33/restaurants?deliveryAreaId=935485&postalCode=1077&lat=52.344931&lng=4.8766245&limit=0&isAccurate=true", headers=headers).json()['restaurants'].items()):

        if restaurant['indicators']['isTestRestaurant']: #test restaurants usually have broken products / may be fake and should not be scraped
            continue
        if i > maxRequests: #after 125 requests STOP
            break
            
        startRestaurant = time()

        restaurantInfo = requests.get(f"https://cw-api.takeaway.com/api/v33/restaurant?slug={restaurant['primarySlug']}", headers=headers)
        restaurantInfo.raise_for_status()
        restaurantInfo = restaurantInfo.json()

        loc = restaurantInfo['location']
        brand = restaurantInfo['brand']

        if brand['name'] == '':
            continue

        menu = restaurantInfo['menu']
        if menu['categories'] is not []:
            categories = [{'productIds':category['productIds'], 'name':category['name']} for category in menu['categories']]
        
        restaurant = {}
        productOptionGroups = []
        optionGroups = []
        options = []
        products = []

        restaurant['slug'] = restaurantInfo['primarySlug']
        restaurant['chain'] = brand['chainId']

        

        restaurant['name'] = brand['name']
        restaurant['restaurantId'] = restaurantInfo['restaurantId']
        restaurant['url'] = f"https://www.thuisbezorgd.nl/{restaurant['slug']}"
        restaurant['website'] = restaurantInfo['minisiteUrl']
        restaurant['logo'] = brand['logoUrl']
        restaurant['address'] = f"{loc['country']}, {loc['streetName']} {loc['streetNumber']}, {loc['postalCode']} {loc['city']}"
        restaurant['slogan'] = brand['slogan']

        
        for productId, product in menu['products'].items():
            newProduct = {}

            variant = product['variants'][0]

            newProduct['productId'] = productId
            newProduct['name'] = product['name']
            newProduct['category'] = None

            if categories:
                newProduct['category'] = getAt([category['name'] for category in categories if productId in category['productIds']], 0)

            newProduct['description'] = getAt(product['description'], 0)
            newProduct['image'] = product['imageUrl']
            newProduct['priceCents'] = variant['prices']['delivery']
            products.append(newProduct)
            
        

            for optionGroupId in variant['optionGroupIds']:
                newProductOptionGroup = {}
                newProductOptionGroup['productId'] = productId
                newProductOptionGroup['optionGroup'] = str(optionGroupId)
                productOptionGroups.append(newProductOptionGroup)

        if products == []:
            continue
            
        for optionGroupId, optionGroup in menu['optionGroups'].items():
            for optionId in optionGroup['optionIds']:
                newOptionGroup = {}
                newOptionGroup['optionGroup'] = optionGroupId
                newOptionGroup['name'] = optionGroup['name']
                newOptionGroup['optionId'] = optionId
                optionGroups.append(newOptionGroup)

        for optionId, option in menu['options'].items():
            newOptionId = {}
            newOptionId['optionId'] = optionId
            newOptionId['name'] = option['name']
            newOptionId['priceCents'] = option['prices']['delivery']

            options.append(newOptionId)

        for tableType in TableTypes:
            connection.createTable(restaurant['slug'], restaurant['chain'], tableType)

        connection.insertInto(TableTypes.Restaurant, restaurant)
        connection.insertInto(TableTypes.ProductOptionGroups, productOptionGroups)
        connection.insertInto(TableTypes.OptionGroups, optionGroups)
        connection.insertInto(TableTypes.OptionIds, options)
        connection.insertInto(TableTypes.Products, products)
        
        timeRestaurant = time() - startRestaurant
        if timeRestaurant > 6:
            print(restaurant['url'])
        print(f"Restaurant time: {timeRestaurant} seconds")
        
    print(f"Total time: {time() - start} seconds")

run(getProducts())
