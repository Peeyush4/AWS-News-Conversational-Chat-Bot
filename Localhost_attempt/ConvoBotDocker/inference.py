from flask import Flask, jsonify, request
from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline
import os
import logging

# Initialize Flask app
app = Flask(__name__)

# Logging configuration
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Global variables
model = None
tokenizer = None
qa_pipeline = None

def initialize_model():
    """
    Load the model and tokenizer.
    """
    global model, tokenizer, qa_pipeline
    model_dir = "/opt/ml/model"  # Update if necessary
    try:
        logger.info("Loading model...")
        if not os.path.exists(os.path.join(model_dir, "model")):
            raise FileNotFoundError("Model directory not found.")
        if not os.path.exists(os.path.join(model_dir, "tokenizer")):
            raise FileNotFoundError("Tokenizer directory not found.")
        
        model = AutoModelForQuestionAnswering.from_pretrained(os.path.join(model_dir, "model"))
        tokenizer = AutoTokenizer.from_pretrained(os.path.join(model_dir, "tokenizer"))
        qa_pipeline = pipeline("question-answering", model=model, tokenizer=tokenizer)
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
def intialize_model_from_huggingface():
    """
    Load the model and tokenizer from Hugging Face directly.
    """
    global model, tokenizer, qa_pipeline
    try:
        logger.info("Loading model from Hugging Face...")
        model_name = "nldemo/Llama-3-8B-Story-Summarization-QLoRA"  # Replace with your desired model
        model = AutoModelForQuestionAnswering.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        qa_pipeline = pipeline("question-answering", model=model, tokenizer=tokenizer)
        logger.info("Model loaded successfully from Hugging Face.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")

# Call initialize_model during startup
intialize_model_from_huggingface()

@app.route('/', methods=['GET'])
def home():
    """
    Root endpoint for basic info.
    """
    return jsonify({"message": "Welcome to the Question Answering API!"}), 200

@app.route('/ping', methods=['GET'])
def ping():
    """
    Health check endpoint required by SageMaker.
    """
    health = model is not None and tokenizer is not None and qa_pipeline is not None
    status = 200 if health else 503
    logger.debug(f"Health check: {'healthy' if health else 'unhealthy'}")
    return jsonify({"status": "healthy" if health else "unhealthy"}), status

@app.route('/invocations', methods=['POST'])
def invocations():
    """
    Inference endpoint to handle prediction requests.
    """
    if qa_pipeline is None:
        logger.error("Model not initialized.")
        return jsonify({"error": "Model not initialized"}), 500

    input_data = request.get_json()
    if not input_data or "question" not in input_data or "context" not in input_data:
        logger.error("Invalid input. Must contain 'question' and 'context'.")
        return jsonify({"error": "Invalid input. Must contain 'question' and 'context'"}), 400

    question = input_data["question"]
    context = input_data["context"]

    try:
        logger.info(f"Received question: {question}")
        result = qa_pipeline(question=question, context=context, max_answer_len=512, min_answer_len=500)
        logger.info("Inference completed successfully.")
        return jsonify({"answer": result["answer"]})
    except Exception as e:
        logger.error(f"Inference error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)