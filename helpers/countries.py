import pycountry
import requests


countries = [country.name for country in pycountry.countries]
print(countries)

country = 'india'
category = None
base_url = "https://newsapi.org/v2/everything"
params = {
    'apiKey': "6f2549f5dca74560a49b6712e4ac8259",
    'q': country if country else category
}

response = requests.get(base_url, params=params)
response.raise_for_status()  # Check for request errors

print(response.json())