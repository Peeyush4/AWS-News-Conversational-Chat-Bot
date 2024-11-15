# AWS-News-Conversational-Chat-Bot

## Create AWS Lambda Function 

1. Search for “AWS Lambda” and click “Create function” 

2. Choose “Author from Scratch”, Runtime to be “Python 3.12” and write a function name and click on “Create function”. 

3. Paste this below code 
```python
import json 

import requests 

import boto3 

import datetime 

 

# Initialize S3 client 

s3 = boto3.client('s3') 

 

def lambda_handler(event, context): 

    # News API URL (replace with your NewsAPI key) 

    url = ('https://newsapi.org/v2/top-headlines?' 

       'country=us&' 

       'apiKey=6f2549f5dca74560a49b6712e4ac8259') 

    # Fetch news data 

    response = requests.get(url) 

     

    if response.status_code == 200: 

        news_data = response.json() 

         

        # Create a unique file name based on current date and time 

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

            'statusCode': response.status_code, 

            'body': json.dumps("Failed to fetch news") 

        } 
```
4. We need to click “Deploy” but when we do so, you cannot run the code when using the test case because there is no requests library. For that reason,  
a. Download requests library in your local computer by first creating an empty folder and then “pip install requests -t .” inside the folder

b. Zip the folder and upload the code.  
c. If needed, write the code lambda_function.py again and bring all the internal folders out. 

6. [Optional] Below the code, click on “Configuration” > “Permissions” and then click on the Role name’s link in the “Execution Role” section. You will be directed to the “IAM > Roles” part, where  

In the permissions section, click on “Add permissions” > “Add policies”. 

Search for “AmazonS3FullAccess” and “Add permissions”. 

## Add triggers 

Now, we need to create triggers.  

1. Click on “Add triggers” in the AWS Lambda section. 

2. In the “Trigger Configuration” section, type “API Gateway”. You can create a new API or use existing API. I used HTTP API. Then click “Add”. 

## Storage  

1. We need to create an S3 bucket. I unchecked “Block all public access” while creating. Click “Create bucket” 

2. Once the bucket is created, go inside the created bucket to view properties, click on “Permissions”, edit the bucket policy below and save. 

```json
{ 

    "Version": "2012-10-17", 

    "Statement": [ 

        { 

            "Effect": "Allow", 

            "Principal": "*", 

            "Action": [ 

                "s3:PutObject", 

                "s3:GetObject" 

            ], 

            "Resource": "arn:aws:s3:::<bucket-name>/*" 

        } 

    ]

} 
```
In the lambda function’s Configuration section, you can use API link to trigger and see it is stored in S3. 




*****UPDATES FROM KRISHNA***

1. file to fetch the query paramter from front-end (basic preprocessing step) and create a url for the lambda to trigger, fetch and store details from the newsapi


## ML code
```python
from transformers import pipeline  
# Load the question-answering pipeline with DistilBERT  
qa_pipeline = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")  

# Define the context and the question  
context = text  
question = "What are today's headlines in the US?"  
# Get the answer  
result = qa_pipeline(question=question,   
                    context=context,       
                    max_answer_len=150,    # Increase max answer length  
                    min_answer_len=20,    # Set a minimum answer length  
                    max_seq_len=512,      # Maximum sequence length for processing (default is 384))  
                    )  

print(f"Answer: {result['answer']}") 
```

## Amazon SageMaker 
Amazon SageMaker: 
1. Search for Amazon SageMaker (go to Domains in Admin Domains).
2. Click on “Create domain” and select on any of those options (I chose “Setup for single user”). And click on “Set up”. Now, wait for the domain to get set up. 
3. Once the domain is setup, click on the domain to see “User profiles” to view all the profiles present. Click on “Launch” after on a profile and click on “Studio”. You will be directed to the SageMaker Studio. 
4. You can see in the Applications section of the Amazon SageMaker Studio. In that section, you can open either JupyterLab or Code Editor, click on “+ Create JupyterLab Space” if you open JupyterLab or “+ Create Code Editor Space”, name it and click on “Create space”. 
5. Once the space is created, click on “Run space” to run it. 
