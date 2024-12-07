import json
from transformers import pipeline
import time
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
start = time.time()
# Load the question-answering pipeline with the pre-trained model
qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2", device=device)

# Get the model and tokenizer from the pipeline
model = qa_pipeline.model
tokenizer = qa_pipeline.tokenizer
end = time.time()
model_path = "./model"
tokenizer_path = "./tokenizer"
qa_pipeline.model.save_pretrained(model_path)  # Save the model
qa_pipeline.tokenizer.save_pretrained(tokenizer_path)  # Save the tokenizer
print("Model and tokenizer loaded successfully")
print(f"Time taken to load model: {end-start} seconds")
# Save the model (weights)
# torch.save(model.state_dict(), 'model.pt')

# Optionally save the tokenizer (you will need this later to use the model again)
# tokenizer.save_pretrained('./tokenizer')
