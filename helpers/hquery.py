import boto3
import json
import logging
import requests
import re
import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
_LOG = logging.getLogger()

# S3 bucket details
INPUT_BUCKET = "your-input-bucket"
OUTPUT_BUCKET = "your-output-bucket"
QUERY_KEY = "input/query.json"
SUMMARY_KEY = "output/summary.json"

# SageMaker configurations
PROCESSING_JOB_NAME = "summarization-job"
ROLE_ARN = "your-sagemaker-execution-role"
HUGGINGFACE_IMAGE_URI = ""

# NewsAPI key
NEWS_API_KEY = "your-newsapi-key"

# Supported countries and categories
COUNTRIES = {
    'united states': 'us',
    'india': 'in',
    'canada': 'ca',
    'germany': 'de',
    'france': 'fr',
    'china': 'cn',
    'brazil': 'br'
}
CATEGORIES = ['politics', 'finance', 'technology', 'sports', 'entertainment', 'health']


def lambda_handler(event, context):
    try:
        # Parse input query
        query = event.get("queryStringParameters", {}).get("q")
        if not query:
            return create_response(400, {"error": "No query provided"})
        
        _LOG.info(f"Received query: {query}")

        # Extract country and category
        country, category = extract_keywords_simple(query)
        if not country or not category:
            return create_response(400, {"error": "Invalid country or category in query"})

        # Fetch news using the News API
        news_data = trigger_news_api(country, category)

        # Save news data to S3
        save_news_to_s3(news_data)

        # Trigger SageMaker processing job
        trigger_sagemaker_processing()

        # Wait for job completion (optional)
        wait_for_processing_job()

        # Retrieve the summarization result from S3
        summary = retrieve_summary_from_s3()

        # Return the summary to the client
        return create_response(200, {"summary": summary})

    except Exception as e:
        _LOG.error(f"Error: {str(e)}", exc_info=True)
        return create_response(500, {"error": "Internal server error"})


def extract_keywords_simple(query):
    """
    Extract country and category keywords using basic string matching.
    """
    query = preprocess_query(query)
    country = None
    category = None

    for c in COUNTRIES.keys():
        if c in query:
            country = c
            break

    for cat in CATEGORIES:
        if cat in query:
            category = cat
            break

    _LOG.info(f"Extracted Country: {country}, Category: {category}")
    return country, category


def preprocess_query(query):
    """
    Preprocess query to lowercase and remove punctuation.
    """
    return re.sub(r'[^\w\s]', '', query.lower())


def trigger_news_api(country, category):
    """
    Fetch news articles from NewsAPI based on country and category.
    """
    base_url = "https://newsapi.org/v2/top-headlines"
    iso_country = COUNTRIES.get(country)
    params = {
        'apiKey': NEWS_API_KEY,
        'country': iso_country,
        'category': category
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        news_data = response.json()
        return news_data
    except requests.exceptions.RequestException as e:
        _LOG.error(f"Error fetching news: {e}")
        return {"error": str(e)}


def save_news_to_s3(news_data):
    """
    Saves news data to S3 with a timestamped filename.
    """
    s3 = boto3.client("s3")
    current_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    file_name = f"news_{current_time}.json"
    json_data = json.dumps(news_data)
    s3.put_object(Bucket=INPUT_BUCKET, Key=f"news/{file_name}", Body=json_data)
    _LOG.info(f"Saved news data to s3://{INPUT_BUCKET}/news/{file_name}")


def trigger_sagemaker_processing():
    """
    Triggers the SageMaker processing job.
    """
    sagemaker = boto3.client("sagemaker")
    response = sagemaker.create_processing_job(
        ProcessingJobName=PROCESSING_JOB_NAME,
        ProcessingResources={
            "ClusterConfig": {
                "InstanceCount": 1,
                "InstanceType": "ml.m5.large",
                "VolumeSizeInGB": 10
            }
        },
        AppSpecification={
            "ImageUri": HUGGINGFACE_IMAGE_URI,
            "ContainerEntrypoint": ["python3", "/opt/ml/processing/input/code/summarization.py"]
        },
        RoleArn=ROLE_ARN,
        ProcessingInputs=[
            {
                "InputName": "input-query",
                "S3Input": {
                    "S3Uri": f"s3://{INPUT_BUCKET}/{QUERY_KEY}",
                    "LocalPath": "/opt/ml/processing/input",
                    "S3DataType": "S3Prefix",
                    "S3InputMode": "File"
                }
            }
        ],
        ProcessingOutputConfig={
            "Outputs": [
                {
                    "OutputName": "summary-output",
                    "S3Output": {
                        "S3Uri": f"s3://{OUTPUT_BUCKET}/output/",
                        "LocalPath": "/opt/ml/processing/output",
                        "S3UploadMode": "EndOfJob"
                    }
                }
            ]
        }
    )
    _LOG.info(f"SageMaker processing job triggered: {response['ProcessingJobArn']}")


def wait_for_processing_job():
    """
    Waits for the SageMaker processing job to complete.
    """
    sagemaker = boto3.client("sagemaker")
    waiter = sagemaker.get_waiter("processing_job_completed_or_stopped")
    waiter.wait(ProcessingJobName=PROCESSING_JOB_NAME)
    _LOG.info("SageMaker processing job completed")


def retrieve_summary_from_s3():
    """
    Retrieves the summarization result from S3.
    """
    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=OUTPUT_BUCKET, Key=SUMMARY_KEY)
    summary_data = json.loads(response["Body"].read().decode("utf-8"))
    _LOG.info(f"Retrieved summary from s3://{OUTPUT_BUCKET}/{SUMMARY_KEY}")
    return summary_data.get("summary", "No summary available")


def create_response(status_code, body):
    """
    Creates a response for the Lambda function.
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        },
        "body": json.dumps(body)
    }
