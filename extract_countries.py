import bs4
import requests
import json

response = requests.get('https://newsapi.org/sources')
html = response.text

# Parse the HTML page
soup = bs4.BeautifulSoup(html, 'html.parser')
# Extract the country names
# countries = [a.text for a in soup.find_all('a')]
# return countries    

country_html = soup.findAll('div', class_='name f3')
country_codes_html = soup.findAll('kbd')

countries = [country.text.strip().lower() for country in country_html]
country_codes = [country_code.text.strip() for country_code in country_codes_html]


# print(countries)
# print(country_codes)

# print(len(countries) == len(country_codes))

country_info = {
    country: code for country, code in zip(countries, country_codes)
}

json.dump(country_info, open('country_info.json', 'w'), indent=4)