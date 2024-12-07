import json
from transformers import pipeline
import torch
from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline
import time
import os
import requests

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
NEWS_API_KEY = "6f2549f5dca74560a49b6712e4ac8259"

start = time.time()
model = AutoModelForQuestionAnswering.from_pretrained(f"./model")
print("Model loaded successfully")
# Reload the tokenizer
tokenizer = AutoTokenizer.from_pretrained('./tokenizer')
end = time.time()

print(f"Time taken to load model: {end-start} seconds")

query = "What are the headlines in teh united states ?"
base_url = "https://newsapi.org/v2/top-headlines"
params = {
    'apiKey': NEWS_API_KEY,
    'country': 'us'
}

response = requests.get(base_url, params=params)
print(response.url)
response.raise_for_status()
news_data = response.json()
context = []
for i, article in enumerate(news_data['articles']):
    context = f"{article['title']}: {article['description']}\n"
    # if i > 10: break
# print(f"Context: {context}")
start = time.time()
pipe = pipeline("question-answering", model=model, tokenizer=tokenizer, device=device)
summary = pipe(question=query,   
                context=context,       
                max_answer_len=100,    # Increase max answer length  
                min_answer_len=50,    # Set a minimum answer length  
                max_seq_len=512,      # Maximum sequence length for processing (default is 384))  
                )["answer"]
end = time.time()
print(f"Summary: {summary}")
print(f"Time taken to summarize: {end-start} seconds")

# Write output back to S3
output_bucket = "outputbucket-123"
output_key = "output/summary.json"
# s3.put_object(Bucket=output_bucket, Key=output_key, Body=json.dumps({"summary": summary}))
