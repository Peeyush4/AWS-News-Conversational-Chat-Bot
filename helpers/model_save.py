import json
from transformers import pipeline
import torch

# Load the question-answering pipeline with the pre-trained model
qa_pipeline = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")

# Get the model and tokenizer from the pipeline
model = qa_pipeline.model
tokenizer = qa_pipeline.tokenizer

# Save the model (weights)
model.save_pretrained('./model')

# Optionally save the tokenizer (you will need this later to use the model again)
tokenizer.save_pretrained('./tokenizer')
