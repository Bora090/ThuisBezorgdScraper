# ThuisBezorgdScraper

# Max Requests

the variable at the top "maxRequests" indicates the amount of restaurants to be scraped

# DB Credentials

Make sure to modify DBCredentials.py with your own credentials

# Change Address To Scrape
To scrape a custom address just go to https://www.thuisbezorgd.nl/ put in your address and look for this request in f12 network tab

https://cw-api.takeaway.com/api/v33/restaurants?deliveryAreaId=933681&postalCode=9721&lat=53.1959519&lng=6.574356099999999&limit=0&isAccurate=true
you can then replace the request here:
```py
for i, (_, restaurant) in enumerate(requests.get("https://cw-api.takeaway.com/api/v33/restaurants?deliveryAreaId=935485&postalCode=1077&lat=52.344931&lng=4.8766245&limit=0&isAccurate=true", headers=headers).json()['restaurants'].items()):
```
with your request


