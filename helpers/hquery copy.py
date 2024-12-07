import json
import requests
import boto3
import datetime
import logging
import spacy
import re
import os

_LOG = logging.getLogger("__name__")


def extract_keywords_with_nlp(query: str):
    """
    Extracts keywords from a given query string using spaCy.

    :param query: The query string to extract keywords from
    :return: A tuple containing the extracted country and category
    """
    # Load spaCy language model
    nlp = spacy.load('en_core_web_sm')
    query = preprocess_query(query)
    # Extract keywords with spaCy
    doc = nlp(query)
    country = None
    category = None
    # Define the possible countries and categories for extraction
    countries = ['united states', 'india', 'canada', 'germany', 'france', 'china', 'brazil']
    categories = ['politics', 'finance', 'technology', 'sports', 'entertainment', 'health']
    # Extract keywords for country
    for ent in doc.ents:
        if ent.label_ == 'GPE' and ent.text.lower() in countries:
            country = ent.text.lower()
    # Extract keywords for category
    for token in doc:
        if token.text.lower() in categories:
            category = token.text.lower()
    _LOG.info(f"Search query: {query} and got Country: {country}, Category: {category}")
    return country, category

def preprocess_query(query: str) -> str:
    """
    Preprocesses a given query string to remove punctuation and convert it to lowercase.

    :param query: The query string to preprocess
    :return: The preprocessed query string
    """
    # Remove punctuation and convert to lowercase
    query = re.sub(r'[^\w\s]', '', query.lower())
    return query

def trigger_news_api(country: str, category: str):
    """
    Fetch news articles from NewsAPI based on country and category.

    :param country: The country to fetch news for
    :param category: The category to fetch news for
    :return: The news data fetched from NewsAPI
    """
    if country and category:
        base_url = "https://newsapi.org/v2/top-headlines"
        # Mapping for country names to NewsAPI codes
        country_mapping = {
            'united states': 'us',
            'india': 'in',
            'canada': 'ca',
            'germany': 'de',
            'france': 'fr',
            'china': 'cn',
            'brazil': 'br'
        }
        iso_country = country_mapping.get(country.lower())
        params = {
            'apiKey': "6f2549f5dca74560a49b6712e4ac8259",
            'country': iso_country,
            'category': category.lower()
        }
    else:
        base_url = "https://newsapi.org/v2/everything"
        params = {
            'apiKey': "6f2549f5dca74560a49b6712e4ac8259",
            'q': country if country else category
        }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Check for request errors
        news_data = response.json()
        return news_data  # Return the news data if successful
    except requests.exceptions.RequestException as e:
        _LOG.error(f"Error fetching news: {e}")
        return {"error": str(e)}

def lambda_handler(event, context): 
    query = event['queryStringParameters']['q']
    country, category = extract_keywords_with_nlp(query)
    if country or category:
        # Fetch news using the trigger_news_api function
        news_data = trigger_news_api(country, category)
        # Initialize S3 client
        s3 = boto3.client('s3')
        # Create a unique file name based on the current date and time
        current_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        file_name = f"news_{current_time}.json"
        # Convert the news data to JSON format
        json_data = json.dumps(news_data)
        # Upload the file to the S3 bucket
        s3.put_object(Bucket='bucket-for-store', Key=file_name, Body=json_data)
        return {
            'statusCode': 200,
            'body': json.dumps(f"News data saved as {file_name}")
        }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps("Could not extract valid country or category from the query.")
        }
