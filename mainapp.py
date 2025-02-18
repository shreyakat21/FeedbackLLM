from flask import Flask, jsonify, request
from dotenv import load_dotenv
import os
import openai
from pinecone import Pinecone, ServerlessSpec
from firestore import initialize_firestore
import uuid

# Load environment variables
load_dotenv()

# Set API keys
openai.api_key = os.getenv('OPENAI_API_KEY')
pinecone_api_key = os.getenv('PINECONE_API_KEY')

# Initialize Flask app
app = Flask(__name__)

# Initialize Firestore
db = initialize_firestore()

# Initialize Pinecone
pc = Pinecone(api_key=pinecone_api_key)
index_name = "lab-reports"
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,  # Dimension of OpenAI's text-embedding-ada-002 model
        metric="cosine",  # Use cosine similarity for text embeddings
        spec=ServerlessSpec(
            cloud="aws",  # Use AWS
            region="us-east-1"  # Supported region for free tier
        )
    )
index = pc.Index(index_name)

# Function to analyze lab report using OpenAI
def analyze_lab_report(lab_report_text, rubric_text):
    prompt = f"Lab Report: {lab_report_text}\nFixed Rubric: {rubric_text}\n\nPlease review the lab report and provide feedback based on the rubric."
    try:
        response = openai.Completion.create(
            model="gpt-3.5-turbo",  # Use GPT-3.5-turbo
            prompt=prompt,
            max_tokens=500,  # Adjust based on your needs
            n=1,
            stop=None,
            temperature=0.7
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Error analyzing lab report: {str(e)}"

# Function to generate embeddings using OpenAI
def get_embedding(text, model="text-embedding-ada-002"):
    response = openai.Embedding.create(input=text, model=model)
    return response['data'][0]['embedding']

# Function to save analysis result to Firestore and Pinecone
def save_analysis_to_storage(student_name, lab_report_text, rubric_text, analysis_result):
    # Combine fields into a single text for embedding
    combined_text = f"Student: {student_name}, Lab Report: {lab_report_text}, Feedback: {analysis_result}"

    # Generate embedding
    embedding = get_embedding(combined_text)

    # Save to Firestore
    data = {
        'student_name': student_name,
        'lab_report': lab_report_text,
        'rubric': rubric_text,
        'analysis_result': analysis_result
    }
    db.collection('lab_reports').add(data)

    # Save to Pinecone
    unique_id = str(uuid.uuid4())  # Generate a unique ID
    metadata = {
        "student_name": student_name,
        "lab_report": lab_report_text,
        "feedback": analysis_result
    }
    index.upsert([(unique_id, embedding, metadata)])

# Route to analyze a lab report and store the results
@app.route('/analyze_lab_report', methods=['POST'])
def analyze_and_store_lab_report():
    # Get data from POST request
    data = request.get_json()
    student_name = data.get('student_name')
    lab_report_text = data.get('lab_report')
    rubric_text = data.get('rubric')
    
    if not student_name or not lab_report_text or not rubric_text:
        return jsonify({'error': 'Student name, lab report, and rubric are required.'}), 400

    # Analyze the lab report using OpenAI API
    analysis_result = analyze_lab_report(lab_report_text, rubric_text)

    # Save the analysis result to Firestore and Pinecone
    save_analysis_to_storage(student_name, lab_report_text, rubric_text, analysis_result)
    
    # Return the analysis result
    return jsonify({'analysis_result': analysis_result})

# Route to fetch all lab report analyses from Firestore
@app.route('/get_lab_reports', methods=['GET'])
def get_lab_reports():
    # Fetch all lab reports from Firestore
    lab_reports_ref = db.collection('lab_reports')
    reports = lab_reports_ref.stream()
    
    report_list = [report.to_dict() for report in reports]
    return jsonify(report_list)

# Route to perform vector-based search
@app.route('/search_lab_reports', methods=['POST'])
def search_lab_reports():
    # Get search query from POST request
    data = request.get_json()
    query_text = data.get('query')
    
    if not query_text:
        return jsonify({'error': 'Search query is required.'}), 400

    # Generate embedding for the query
    query_embedding = get_embedding(query_text)

    # Query the Pinecone index
    results = index.query(
        vector=query_embedding,
        top_k=5,  # Number of results to return
        include_metadata=True
    )

    # Format results
    search_results = [{
        "student_name": match['metadata']['student_name'],
        "lab_report": match['metadata']['lab_report'],
        "feedback": match['metadata']['feedback'],
        "similarity_score": match['score']
    } for match in results["matches"]]
    
    return jsonify(search_results)

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)