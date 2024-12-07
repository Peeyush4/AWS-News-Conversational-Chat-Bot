import json
import boto3
from transformers import pipeline
import requests

def main():
    # Load summarization pipeline
    model = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")

    # Read input query from S3
    s3 = boto3.client("s3")
    bucket = "inputbucket-123"
    key = "input/query.json"
    query_obj = s3.get_object(Bucket=bucket, Key=key)
    input_data = json.loads(query_obj["Body"].read().decode("utf-8"))

    # Perform summarization
    query = input_data["query"]
    print(f"Query: {query}")
    context_obj = s3.get_object(Bucket=bucket, Key=input_data['file_name'])
    context_data = json.loads(context_obj["Body"].read().decode("utf-8"))

    context = ''
    for i, article in enumerate(context_data['articles']):
        context += f"{article['title']}: {article['description']}\n"
        if i > 10: break
    print(f"Context: {context}")

    summary = model(question=query,   
                    context=context,       
                    max_answer_len=100,    # Increase max answer length  
                    min_answer_len=20,    # Set a minimum answer length  
                    max_seq_len=512,      # Maximum sequence length for processing (default is 384))  
                    )["answer"]

    # Write output back to S3
    output_bucket = "outputbucket-123"
    output_key = "output/summary.json"
    s3.put_object(Bucket=output_bucket, Key=output_key, Body=json.dumps({"summary": summary}))

if __name__ == "__main__":
    main()