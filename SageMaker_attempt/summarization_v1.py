import json
import boto3
import requests
from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline
import os


# Load the model and tokenizer from S3
def load_model_from_s3(s3, bucket, prefix, local_dir):
    os.makedirs(local_dir, exist_ok=True)
    # Download all files from S3
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    if "Contents" in response:
        for obj in response["Contents"]:
            key = obj["Key"]
            file_name = os.path.basename(key)
            local_path = os.path.join(local_dir, file_name)
            print(f"Downloading {key} to {local_path}...")
            s3.download_file(bucket, key, local_path)
    else:
        print("No objects found in the specified prefix.")
        exit(1)

def main():
    s3 = boto3.client("s3")
    bucket = "inputbucket-123"

    # Load the model and tokenizer from S3
    load_model_from_s3(s3, bucket, "model/model", "./model")
    load_model_from_s3(s3, bucket, "model/tokenizer", "./tokenizer")
    print("Model and tokenizer loaded successfully")
    # Reload the model
    model = AutoModelForQuestionAnswering.from_pretrained('model')
    print("Model loaded successfully")
    # Reload the tokenizer
    tokenizer = AutoTokenizer.from_pretrained('tokenizer')
    print("Model and Tokenizer loaded successfully")
    # Now you can use the model for question answering
    qa_pipeline = pipeline("question-answering", model=model, tokenizer=tokenizer)

    # Read input query from S3
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
    print(f"Summary: {summary}")
    # Write output back to S3
    output_bucket = "outputbucket-123"
    output_key = "output/summary.json"
    s3.put_object(Bucket=output_bucket, Key=output_key, Body=json.dumps({"summary": summary}))

if __name__ == "__main__":
    main()