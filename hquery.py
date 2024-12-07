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
INPUT_BUCKET = "inputbucket-123"
OUTPUT_BUCKET = "outputbucket-123"
QUERY_KEY = "input/query.json"
SUMMARY_KEY = "output/summary.json"

# SageMaker configurations
PROCESSING_JOB_NAME = f"summarization-job-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
ROLE_ARN = "arn:aws:iam::438465147520:role/service-role/SageMaker-ConversationalBot"
# HUGGINGFACE_IMAGE_URI = "763104351884.dkr.ecr.us-east-1.amazonaws.com/huggingface-pytorch-inference:1.13.1-transformers4.26.1-cpu-py39"
HUGGINGFACE_IMAGE_URI = "438465147520.dkr.ecr.us-east-1.amazonaws.com/cloud/conversational-bot:v1"
# NewsAPI key
NEWS_API_KEY = "6f2549f5dca74560a49b6712e4ac8259"

# Supported countries and categories
COUNTRIES = {
    "argentina": "ar",
    "australia": "au",
    "austria": "at",
    "belgium": "be",
    "brazil": "br",
    "bulgaria": "bg",
    "canada": "ca",
    "china": "cn",
    "colombia": "co",
    "cuba": "cu",
    "czech republic": "cz",
    "egypt": "eg",
    "france": "fr",
    "germany": "de",
    "greece": "gr",
    "hong kong": "hk",
    "hungary": "hu",
    "india": "in",
    "indonesia": "id",
    "ireland": "ie",
    "israel": "il",
    "italy": "it",
    "japan": "jp",
    "latvia": "lv",
    "lithuania": "lt",
    "malaysia": "my",
    "mexico": "mx",
    "morocco": "ma",
    "netherlands": "nl",
    "new zealand": "nz",
    "nigeria": "ng",
    "norway": "no",
    "philippines": "ph",
    "poland": "pl",
    "portugal": "pt",
    "romania": "ro",
    "russia": "ru",
    "saudi arabia": "sa",
    "serbia": "rs",
    "singapore": "sg",
    "slovakia": "sk",
    "slovenia": "si",
    "south africa": "za",
    "south korea": "kr",
    "sweden": "se",
    "switzerland": "ch",
    "taiwan": "tw",
    "thailand": "th",
    "turkey": "tr",
    "uae": "ae",
    "ukraine": "ua",
    "united kingdom": "gb",
    "united states": "us",
    "venuzuela": "ve"
}
CATEGORIES = ['politics', 'finance', 'technology', 'sports', 'entertainment', 'health']


# Initialize the Bedrock client
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)

MODEL_ID = "us.meta.llama3-2-90b-instruct-v1:0"  # The Llama model ID


def lambda_handler(event, context):
    try:
        # Parse input query
        print(f"Event: {event}, time: {datetime.datetime.now()}")
        query = event.get("queryStringParameters", {}).get("q")
        if not query:
            return create_response(400, {"error": "No query provided"})

        print(f"Received query: {query}, time: {datetime.datetime.now()}")

        # Extract country and category
        country, category = extract_keywords_simple(query)
        print(f"Country: {country} and Category: {category}")
        if not (country or category):
            return create_response(400, {"error": "Invalid country or category in query"})

        # Fetch news using the News API
        news_data = trigger_news_api(country, category)
        print(f"API triggered, time: {datetime.datetime.now()}")

        # Save news data to S3
        file_name = save_news_to_s3(news_data, query)
        print(f"Saved news, time: {datetime.datetime.now()}")

        # Run inference using endpoint
        summary = infer_with_endpoint(query, file_name)
        print(f"Summary: {summary}, time: {datetime.datetime.now()}")

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

    print(f"Extracted Country: {country}, Category: {category}")
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
    params = {
        'apiKey': NEWS_API_KEY,
    }
    
    if country: params['country'] = COUNTRIES.get(country)
    if category: params['category'] = category
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        news_data = response.json()
        print(f"News data: ", news_data)
        if news_data['totalResults'] == 0:
            base_url = "https://newsapi.org/v2/everything"
            params = {
                'apiKey': NEWS_API_KEY,    
            }
            if country: params['q'] = country
            elif category: params['q'] = category
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            news_data = response.json()
            print("News data v2", news_data)
            assert news_data['totalResults'] != 0, "No news results" 
        return news_data
    except requests.exceptions.RequestException as e:
        _LOG.error(f"Error fetching news: {e}")
        return {"error": str(e)}

def save_news_to_s3(news_data, query):
    """
    Saves news data to S3 with a timestamped filename.
    """
    s3 = boto3.client("s3")
    current_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    file_name = f"news_{current_time}.json"
    json_data = json.dumps(news_data)
    s3.put_object(Bucket=INPUT_BUCKET, Key=f"news/{file_name}", Body=json_data)
    s3.put_object(Bucket=INPUT_BUCKET, Key=QUERY_KEY, Body=json.dumps({'query': query, 'file_name': f"news/{file_name}"}))

    print(f"Saved news data to s3://{INPUT_BUCKET}/news/{file_name}")
    return file_name

def trigger_sagemaker_processing(file_name):
    """
    Triggers the SageMaker processing job.
    """
    sagemaker = boto3.client("sagemaker")
    try:
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
                "ContainerEntrypoint": ["python3", "/opt/ml/processing/data/summarization.py"]
            },
            RoleArn=ROLE_ARN,
            ProcessingInputs=[
                #Input: query and news-info
                {
                    "InputName": "input-query",
                    "S3Input": {
                        "S3Uri": f"s3://{INPUT_BUCKET}/{QUERY_KEY}",
                        "LocalPath": "/opt/ml/processing/data/input",
                        "S3DataType": "S3Prefix",
                        "S3InputMode": "File"
                    }
                },
                {
                    "InputName": "news-info",
                    "S3Input": {
                        "S3Uri": f"s3://{INPUT_BUCKET}/news/{file_name}",
                        "LocalPath": "/opt/ml/processing/data/news",
                        "S3DataType": "S3Prefix",
                        "S3InputMode": "File"
                    }
                },
                #Code: summarization.py
                {
                    "InputName": "code",
                    "S3Input": {
                        "S3Uri": f"s3://{INPUT_BUCKET}/summarization.py",
                        "LocalPath": "/opt/ml/processing/data",
                        "S3DataType": "S3Prefix",
                        "S3InputMode": "File"
                    }
                },
                # ML: model and tokenizer
                {
                    "InputName": "model-config",
                    "S3Input": {
                        "S3Uri": f"s3://{INPUT_BUCKET}/ML_model/model/config.json",
                        "LocalPath": "/opt/ml/processing/data/model",
                        "S3DataType": "S3Prefix",
                        "S3InputMode": "File"
                    }
                },
                {
                    "InputName": "model-parameters",
                    "S3Input": {
                        "S3Uri": f"s3://{INPUT_BUCKET}/ML_model/model/model.safetensors",
                        "LocalPath": "/opt/ml/processing",
                        "S3DataType": "ManifestFile",
                        "S3InputMode": "Pipe"
                    }
                },
                {
                    "InputName": "model-tokenizer-token-map",
                    "S3Input": {
                        "S3Uri": f"s3://{INPUT_BUCKET}/ML_model/tokenizer/special_tokens_map.json",
                        "LocalPath": "/opt/ml/processing/data/tokenizer",
                        "S3DataType": "S3Prefix",
                        "S3InputMode": "File"
                    }
                },
                # {
                #     "InputName": "model-tokenizer-config",
                #     "S3Input": {
                #         "S3Uri": f"s3://{INPUT_BUCKET}/ML_model/tokenizer/tokenizer_config.json",
                #         "LocalPath": "/opt/ml/processing/data/tokenizer",
                #         "S3DataType": "S3Prefix",
                #         "S3InputMode": "File"
                #     }
                # },
                # {
                #     "InputName": "model-tokenizer",
                #     "S3Input": {
                #         "S3Uri": f"s3://{INPUT_BUCKET}/ML_model/tokenizer/tokenizer.json",
                #         "LocalPath": "/opt/ml/processing/data/tokenizer",
                #         "S3DataType": "S3Prefix",
                #         "S3InputMode": "File"
                #     }
                # },
                # {
                #     "InputName": "model-tokenizer-vocab",
                #     "S3Input": {
                #         "S3Uri": f"s3://{INPUT_BUCKET}/ML_model/tokenizer/vocab.txt",
                #         "LocalPath": "/opt/ml/processing/data/tokenizer",
                #         "S3DataType": "S3Prefix",
                #         "S3InputMode": "File"
                #     }
                # },
                # {
                #     "InputName": "model",
                #     "S3Input": {
                #         "S3Uri": f"s3://{INPUT_BUCKET}/ML_model/ML_model.zip",
                #         "LocalPath": "/opt/ml/processing/data",
                #         "S3DataType": "S3Prefix",
                #         "S3InputMode": "Pipe",
                #         "S3CompressionType": "Gzip"
                #     }
                # },
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
        print(f"SageMaker processing job triggered: {response['ProcessingJobArn']}")
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print(f"Full exception: {e.response}")
        print(e.__traceback__)
        raise

def wait_for_processing_job():
    """
    Waits for the SageMaker processing job to complete.
    """
    sagemaker = boto3.client("sagemaker")
    waiter = sagemaker.get_waiter("processing_job_completed_or_stopped")
    waiter.wait(ProcessingJobName=PROCESSING_JOB_NAME)
    print("SageMaker processing job completed")

def retrieve_summary_from_s3():
    """
    Retrieves the summarization result from S3.
    """
    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=OUTPUT_BUCKET, Key=SUMMARY_KEY)
    summary_data = json.loads(response["Body"].read().decode("utf-8"))
    print(f"Retrieved summary from s3://{OUTPUT_BUCKET}/{SUMMARY_KEY}")
    return summary_data.get("summary", "No summary available")

def create_response(status_code, body):
    """
    Creates a response for the Lambda function.
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        },
        "body": json.dumps(body)
    }

def infer_with_endpoint(query, file_name):
    """
    Sends a request to the inference endpoint to process the summarization.
    """
    # S3 client to fetch news data
    s3 = boto3.client("s3")
    print(f"File name verification: {file_name}")
    response = s3.get_object(Bucket=INPUT_BUCKET, Key=f"news/{file_name}")
    news_data = json.loads(response["Body"].read().decode("utf-8"))
    print("Inferring with endpoints:", news_data)
    # Prepare payload for the endpoint
    context = ""
    for article in news_data["articles"]:
        context += f"{article['title']}: {article['description']}\n"
    # payload = {
    #     "question": query, #"Summarize the news articles",
    #     "context": context,
    # }

    # Send request to the inference endpoint
    try:
        # endpoint_url = "https://cdcb-100-15-135-165.ngrok-free.app/invocations"
        # endpoint_url = "https://8741-100-15-135-165.ngrok-free.app/invocations"
        # headers = {"Content-Type": "application/json"}
        # response = requests.post(endpoint_url, headers=headers, json=payload)
        # response.raise_for_status()
        p = f"query: {query} Answer in 150 words. "
        if context:
            p += f"context: {context}"

        messages = [
            {
            "role": "user",
            "content": [{"text": p}]
            }
        ]
        response = bedrock_runtime.converse(
                modelId=MODEL_ID,
                messages=messages
            )
        generated_text = response['output']['message']['content'][0]['text']
        # result = response.json()
        # print(f"Inference result: {result}")
        # return result.get("answer", "No summary available")
        return generated_text
    except requests.exceptions.RequestException as e:
        _LOG.error(f"Error calling inference endpoint: {e}")
        return {"error": str(e)}
