from PIL import Image
import logging
import boto3
import json
import requests
import base64
from botocore.exceptions import ClientError
from io import BytesIO
import time
import uuid
from boto3.dynamodb.conditions import Key
import io


# Initialize the Bedrock client
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('chatHistory')


MODEL_ID = "us.meta.llama3-2-90b-instruct-v1:0"  # The Llama model ID

# URL for the image you want to send to the model
currentPage =''
p = ''
def newPage(pageURL):
    global currentPage
    currentPage = pageURL

def promptUpdate(data):
    global p
    p = p + data


def lambda_handler(event, context):
    #print('Event: ', json.dumps(event))

    requestBody = json.loads(event['body'])
    timestamp = int(time.time() * 1000)  # Current timestamp in milliseconds
    action = requestBody.get('action', '')
    session_id = requestBody.get('session_id', str(uuid.uuid4()))

    # print(action)
    if action == 'delete':
        print("Delete session ID", session_id)
        result = delete_chat_history(session_id)
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': result
            })
        } 


    elif action == 'ask':

        ImageURL = requestBody['imageContext']
        pageContent = requestBody['pageContent']
        prompt = requestBody['prompt']
        pageURL = requestBody['pageURL']
        
        # print(pageContent)
        # print("Image URL", ImageURL)
    #     print(prompt)
    #     print(pageURL)
        # print(session_id)
        try:
            if currentPage != pageURL:
                promptUpdate(pageContent)
                promptUpdate(prompt)
                #print(p)
                if ImageURL == '': 
                    messages = [
                        {
                        "role": "user",
                        "content": [{"text": p}]
                        }
                    ]

                else:
                    imageData = requests.get(ImageURL).content
                    print("read image data")

                    byteImgIO = BytesIO(imageData)
                    image = Image.open(byteImgIO)

                    # image = Image.open(BytesIO(imageData))
                    width, height = image.size
                    format = image.format
                    print("format", format)
                    # Check if the image exceeds the resolution limit
                    if max(width, height) > 1120:
                        # Determine the scaling factor to make the longer side 1120 pixels
                        scaling_factor = 1120 / max(width, height)
                        new_width = int(width * scaling_factor)
                        new_height = int(height * scaling_factor)
                        
                        # Resize the image
                        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        imageData = BytesIO()
                        image.save(imageData, format=format)  # Formats like 'JPEG' require uppercase
                        imageData.seek(0)
                        imageData = imageData.getvalue()
                    format = format.lower()
                    messages = [    
                {
                    "role": "user",
                    "content": [
                        {                
                            "text": p
                        },
                        {                
                            "image": {
                                "format": format,
                                "source": {
                                    "bytes":imageData
                            }
                            }}
                        ]
                    }
                ]
                newPage(pageURL)
            else:
                promptUpdate(prompt)
                #print(p)
                if ImageURL == '': 
                    messages = [
                        {
                        "role": "user",
                        "content": [{"text": p}]
                        }
                        ]
                #currentPage = pageURL
                else:
                    imageData = requests.get(ImageURL).content
                    print('Image data:')
                    image = Image.open(BytesIO(imageData))
                    width, height = image.size
                    format = image.format
                    print("format: ", format)
                    # Check if the image exceeds the resolution limit
                    if max(width, height) > 1120:
                        # Determine the scaling factor to make the longer side 1120 pixels
                        scaling_factor = 1120 / max(width, height)
                        new_width = int(width * scaling_factor)
                        new_height = int(height * scaling_factor)
                        
                        # Resize the image
                        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        imageData = BytesIO()
                        image.save(imageData, format=format)  # Formats like 'JPEG' require uppercase
                        imageData.seek(0)
                        imageData = imageData.getvalue()
                    format = format.lower()
                    messages = [    
                {
                    "role": "user",
                    "content": [
                        {                
                            "text": p
                        },
                        {                
                            "image": {
                                "format": format,
                                "source": {
                                    "bytes":imageData
                            }
                            }}
                        ]
                    }
                ]
                #     # Call the Bedrock Converse API
            response = bedrock_runtime.converse(
                modelId=MODEL_ID,
                messages=messages
            )
            
            # Extract the response content
            generated_text = response['output']['message']['content'][0]['text']
            promptUpdate(generated_text)

            table.put_item(
                Item={
                    'sessionId': session_id,
                    'timestamp': timestamp,
                    'question': prompt,
                    'answer': generated_text,
                    'ImageURL': ImageURL,
                    'pageURL': pageURL,
                    'pageContent': pageContent
                }            
            )

            # Construct the response to return to the client
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'prompt':  "what is this",
                    'response': generated_text
                })
            }
        except Exception as e:
            # Handle any errors and return an error response
            print(f"Error: {str(e)}")   
    
        
def delete_chat_history(session_id):
    print("delete chat history function")
    try:
        print("inside try")
        # Scan for items with the given session_id
        response = table.scan(
            FilterExpression=Key('sessionId').eq(session_id)
        )
        items = response['Items']
        # print(session_id)

        # Delete each item
        with table.batch_writer() as batch:
            for item in items:
                batch.delete_item(
                    Key={
                        'sessionId': item['sessionId'],
                        'timestamp': item['timestamp']
                    }
                )
        return f"Deleted {len(items)} items for session {session_id}."
    except Exception as e:
        return f"Error deleting items: {str(e)}"
