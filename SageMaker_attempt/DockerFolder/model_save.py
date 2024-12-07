import json
from transformers import pipeline
import time

start = time.time()
# Load the question-answering pipeline with the pre-trained model
qa_pipeline = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")

# Get the model and tokenizer from the pipeline
model = qa_pipeline.model
tokenizer = qa_pipeline.tokenizer
end = time.time()
print("Model and tokenizer loaded successfully")
print(f"Time taken to load model: {end-start} seconds")
# Save the model (weights)
# torch.save(model.state_dict(), 'model.pt')

# Optionally save the tokenizer (you will need this later to use the model again)
# tokenizer.save_pretrained('./tokenizer')
