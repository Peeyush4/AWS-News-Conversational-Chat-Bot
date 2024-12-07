import json
import boto3
import requests
from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline
import os


def main():
    s3 = boto3.client("s3")
    bucket = "inputbucket-123"
    # Reload the model
    model = AutoModelForQuestionAnswering.from_pretrained('model')
    print("Model loaded successfully")
    # Reload the tokenizer
    tokenizer = AutoTokenizer.from_pretrained('tokenizer')
    print("Model and Tokenizer loaded successfully")
    # Now you can use the model for question answering
    qa_pipeline = pipeline("question-answering", model=model, tokenizer=tokenizer)

    # Read input query from S3
    # key = "input/query.json"
    # query_obj = s3.get_object(Bucket=bucket, Key=key)
    # input_data = json.loads(query_obj["Body"].read().decode("utf-8"))
    input_data = json.load(open("input/query.json"))

    # Perform summarization
    query = input_data["query"]
    print(f"Query: {query}")    
    # context_obj = s3.get_object(Bucket=bucket, Key=input_data['file_name'])
    # context_data = json.loads(context_obj["Body"].read().decode("utf-8"))
    context_data = json.load(open(input_data['file_name'])) 
    context = ''
    for i, article in enumerate(context_data['articles']):
        context += f"{article['title']}: {article['description']}\n"
        if i > 10: break
    print(f"Context: {context}")

    summary = qa_pipeline(question=query,   
                    context=context,       
                    max_answer_len=100,    # Increase max answer length  
                    min_answer_len=20,    # Set a minimum answer length  
                    max_seq_len=512,      # Maximum sequence length for processing (default is 384))  
                    )["answer"]
    print(f"Summary: {summary}")
    
    # Write output to local file
    os.makedirs("output", exist_ok=True)
    with open("output/summary.json", "w") as f:
        f.write(json.dumps({"summary": summary}))
    # Write output back to S3
    # output_bucket = "outputbucket-123"
    # output_key = "output/summary.json"
    # s3.put_object(Bucket=output_bucket, Key=output_key, Body=json.dumps({"summary": summary}))

if __name__ == "__main__":
    main()