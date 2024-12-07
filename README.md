# Cloud-Based News Chatbot

## Abstract
This project is a cloud-based, AI-powered chatbot designed to deliver concise news summaries tailored to user queries. The chatbot leverages serverless technologies and advanced machine learning models to fetch, process, and summarize news articles in real time.

---

## Problem Statement
The overwhelming volume of online news makes it challenging for users to find relevant information efficiently. This chatbot addresses the issue by automating the retrieval and summarization of news articles based on user queries, providing a user-friendly and accessible solution.

---

## Proposed Solution
- **AI-Powered Chatbot**: Uses cloud technologies for real-time news summaries.  
- **Serverless Architecture**: Ensures scalability and cost efficiency.  
- **Accessible**: Available via any modern web browser.  

---

## Project Workflow
1. **Query Input**: User submits a query through a web interface.
2. **API Gateway**: Triggers AWS Lambda.
3. **AWS Lambda**: Extracts keywords and fetches articles using NewsAPI.
4. **AWS Bedrock**: Processes and summarizes articles using ML models.
5. **S3 Storage**: Stores processed data for easy retrieval.
6. **Response**: Chatbot returns a concise summary.

---

## Key Features
- Real-time news retrieval using NewsAPI.
- Summarization with state-of-the-art machine learning models.
- Fully serverless architecture for scalability.
- Supports multiple categories and countries.
- Accessible through any web browser.

---

## Permissions and Roles

### **API Gateway**  
- **AmazonAPIGatewayAdministrator**: Manage API Gateway configurations.  
- **AmazonAPIGatewayInvokeFullAccess**: Allows invoking deployed APIs.  
- **AmazonAPIGatewayPushToCloudWatchLogs**: Pushes API logs to CloudWatch.

### **Lambda Function**  
- **AWSLambdaBasicExecutionRole**: Logs Lambda function activity to CloudWatch.  
- **AWSLambdaS3ExecutionRole**: Access permissions for reading/writing to S3.  
- **AWSLambdaRoleWithSNS**: Triggers and communicates with SNS if required.  

### **S3 Storage**  
- **AmazonS3FullAccess**: Grants full read/write permissions for buckets.  
- **Bucket-Specific Policy**: Restrict access to specific resources:  
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "s3:GetObject",
          "s3:PutObject"
        ],
        "Resource": "arn:aws:s3:::<your-bucket-name>/*"
      }
    ]
  }
---

## Key Features
- Real-time news retrieval using NewsAPI.
- Summarization with state-of-the-art machine learning models.
- Fully serverless architecture for scalability.
- Supports multiple categories and countries.
- Accessible through any web browser.

---

## AWS Services Used
1. **API Gateway**: Manages HTTP requests and triggers workflows.
2. **AWS Lambda**: Serverless compute for event handling.
3. **S3 Storage**: Stores raw and processed news articles.
4. **AWS Bedrock**: Executes large language models for summarization.
5. **CloudWatch**: Logs system activity for debugging.
6. **Amazon SageMaker**: Manages ML models and performs summarization.
7. **ECR (Elastic Container Registry)**: Stores Docker images for SageMaker.

---

## Technical Details
- **Model Used**: `us.meta.llama3-2-90b-instruct-v1:0`.
- **Query Format**: `"query: {Query} Answer in 150 words. context: {context}"`.
- **Languages**: Python for backend, HTML/CSS/JavaScript for frontend.
- **Development Tools**: Visual Studio Code, AWS Console.

---

## Challenges and Solutions
### Challenges
- Slow execution with early models (~3 minutes per query).
- API Gateway timeout (30 seconds).
- Inefficient handling of larger ML models.

### Solutions
- Shifted to AWS Bedrock for faster inference (23 seconds).
- Eliminated dependency on local compute/storage using cloud-native solutions.

---

## Future Prospects
- Integrate additional data sources for enriched context.
- Optimize the pipeline to reduce costs further.
- Enable logging features for chat history using DynamoDB.
- Deploy on messaging platforms like WhatsApp.
- Improve frontend design and user experience.
- Mitigate AI hallucinations by validating model outputs.

---

## Team Contributions
- **Krishna Taduri**: Developed the initial pipeline and frontend. Explored integrations with SNS, SQS, and DynamoDB.
- **Peeyush Dyavarashetty**: Debugged DistilBERT errors, optimized tokenization, and finalized Bedrock for inference.
- **Rahul Velaga**: Validated models, tested Lambda, and worked on local ML environments.
- **Subha Venkat Milind Manda**: Drafted the final project report.
- **Srijinesh Alanka**: Built a React interface, studied relevant literature, and structured the report.

---

## Repository
GitHub: [AWS-News-Conversational-Chat-Bot](https://github.com/Peeyush4/AWS-News-Conversational-Chat-Bot)
