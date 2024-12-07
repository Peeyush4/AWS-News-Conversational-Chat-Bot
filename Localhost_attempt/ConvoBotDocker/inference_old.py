import json
from transformers import pipeline

def model_fn(model_dir):
    """
    Load the question-answering model.
    This function is invoked once when the endpoint is created.
    """
    model = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")
    return model

def input_fn(input_data, content_type):
    """
    Process the input data sent to the endpoint.
    """
    if content_type == "application/json":
        input_dict = json.loads(input_data)
        return input_dict
    else:
        raise ValueError(f"Unsupported content type: {content_type}")

def predict_fn(input_data, model):
    """
    Perform inference using the loaded model and input data.
    """
    query = input_data["query"]
    context = input_data["context"]

    # Perform question answering
    result = model(
        question=query,
        context=context,
        max_answer_len=100,  # Max answer length
        min_answer_len=20,   # Min answer length
    )

    # Return the answer
    return {"summary": result["answer"]}

def output_fn(prediction, accept):
    """
    Format the output data for the response.
    """
    if accept == "application/json":
        return json.dumps(prediction), "application/json"
    else:
        raise ValueError(f"Unsupported accept type: {accept}")