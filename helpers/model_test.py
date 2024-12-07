from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline
import requests
import time
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
NEWS_API_KEY = "6f2549f5dca74560a49b6712e4ac8259"
model_name = "deepset/roberta-large-squad2"

query = "What are the headlines in the united states ?"
base_url = "https://newsapi.org/v2/top-headlines"
params = {
    'apiKey': NEWS_API_KEY,
    'country': 'us'
}

def get_context():
    response = requests.get(base_url, params=params)
    print(response.url)
    response.raise_for_status()
    news_data = response.json()
    context = ""
    for i, article in enumerate(news_data['articles']):
        context += f"{article['title']}: {article['description']} "

    print(context)
    return context

query, context = "What are the news headlines in the United States?", get_context()

# b) Load model & tokenizer
model = AutoModelForQuestionAnswering.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# c) Load the pipeline
start = time.time()
pipe = pipeline("question-answering", model=model, tokenizer=tokenizer, device=device)
summary = pipe(question=query,   
                context=context,       
                # max_answer_len=512,    # Increase max answer length  
                min_answer_len=400,    # Set a minimum answer length  
                max_seq_len=512,      # Maximum sequence length for processing (default is 384))  
                )["answer"]
end = time.time()
print(f"Time taken to summarize: {end-start} seconds")
print(f"Summary: {summary}")