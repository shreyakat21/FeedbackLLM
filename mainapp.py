from flask import Flask, jsonify, request, render_template, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
import time
from firestore import initialize_firestore
import logging
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import pdfplumber
import hashlib

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = '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'  # Replace with your OpenAI API key
OPENAI_API_ENDPOINT = 'https://api.openai.com/v1'

app = Flask(__name__)
CORS(app, resources={r"/analyze_lab_report": {"origins": "http://127.0.0.1:5000"}})
db = initialize_firestore()

def extract_text_from_pdf(file_storage) -> str:
    """Extract text from a PDF file."""
    try:
        with pdfplumber.open(file_storage) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            return text.strip() if text else "No text extracted from PDF"
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return f"Error extracting text: {str(e)}"

def generate_input_hash(student_name: str, lab_report_text: str, rubric_text: str) -> str:
    """Generate a unique hash for the input combination."""
    input_string = f"{student_name}:{lab_report_text}:{rubric_text}"
    return hashlib.sha256(input_string.encode('utf-8')).hexdigest()

def get_cached_result(input_hash: str) -> str:
    """Check Firestore for a cached result."""
    doc_ref = db.collection('feedback_cache').document(input_hash)
    doc = doc_ref.get()
    if doc.exists:
        logger.debug(f"Found cached result for hash: {input_hash}")
        return doc.to_dict().get('analysis_result', '')
    return None

def cache_result(input_hash: str, analysis_result: str):
    """Cache the result in Firestore."""
    db.collection('feedback_cache').document(input_hash).set({
        'analysis_result': analysis_result,
        'timestamp': time.time()
    })
    logger.debug(f"Cached result for hash: {input_hash}")

def analyze_lab_report(lab_report_text: str, rubric_text: str, student_name: str) -> str:
    logger.debug("Starting OpenAI analysis")
    max_retries = 3
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Generate a unique hash for the input
    input_hash = generate_input_hash(student_name, lab_report_text, rubric_text)
    
    # Check cache first
    cached_result = get_cached_result(input_hash)
    if cached_result:
        return cached_result

    # Revised prompt based on your examples
    prompt = f"""
    Lab Report: {lab_report_text}
    Rubric: {rubric_text}
    Student Name: {student_name}

    You are an expert instructor providing feedback on the lab report based on its content and the provided rubric. Generate two versions of feedback inspired by the following style guidelines, using the tone, detail, and structure from the examples provided:

    1. "Mastery Feedback:" - Deliver high-quality feedback that aligns with "Mastery/Exemplary (4)" examples:
       - Provide specific, credible praise tied to concrete examples from the report (e.g., "Your discussion of how transgenic C. elegans exhibit reduced habituation compared to wild-type connects well to the role of dopamine in behavioral responses").
       - Offer detailed, actionable suggestions for improvement (e.g., "Consider discussing how this specific mechanism might differ from other systems relating to habituation").
       - Emphasize content and scientific reasoning over superficial issues.
       - Encourage dialogue (e.g., "Let me know if you’d like further guidance! I’m here to help").
       - Be supportive and clear, ensuring feedback is usable for future drafts.

    2. "Developing Feedback:" - Deliver lower-quality feedback that aligns with "Developing (2)" examples:
       - Offer vague or general praise (e.g., "Your report is well-organized and easy to follow overall").
       - Provide superficial or unclear criticism (e.g., "The discussion section could use more detail").
       - Focus on minor issues like formatting over content (e.g., "Check that the figure captions are consistent").
       - Avoid specific guidance or actionable steps.
       - Keep it brief and less engaging, with unclear invitations for dialogue if any.

    Use the lab report content to generate feedback that feels authentic and relevant. Do not separate feedback into 'strength' or 'improvement' sections; write each as a single, cohesive paragraph. Format your response as:
    Mastery Feedback: [Your feedback here]\n\nDeveloping Feedback: [Your feedback here]
    """

    for attempt in range(max_retries):
        try:
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0  # Deterministic output
            }
            logger.debug(f"Sending request to {OPENAI_API_ENDPOINT}/chat/completions")
            response = requests.post(
                f"{OPENAI_API_ENDPOINT}/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()['choices'][0]['message']['content'].strip()
            logger.debug(f"OpenAI response: {result}")
            
            # Cache the result
            cache_result(input_hash, result)
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Feedback attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return f"Error generating feedback: {str(e)}"

def save_analysis_to_storage(student_name: str, lab_report_text: str, rubric_text: str, analysis_result: str) -> str:
    logger.debug("Saving to Firestore")
    data = {
        'student_name': student_name,
        'lab_report': lab_report_text,
        'rubric': rubric_text,
        'analysis_result': analysis_result if analysis_result else "No feedback received"
    }
    doc_ref = db.collection('lab_reports').add(data)
    logger.debug("Saved to Firestore")
    return doc_ref[1].id

@app.route('/analyze_lab_report', methods=['POST'])
def analyze_and_store_lab_report():
    logger.debug("Received POST request to /analyze_lab_report")
    
    if 'student_name' not in request.form or 'lab_report' not in request.files or 'rubric' not in request.files:
        logger.error("Missing required fields")
        return jsonify({'error': 'Student name, lab report PDF, and rubric PDF are required.'}), 400

    student_name = request.form.get('student_name')
    lab_report_file = request.files['lab_report']
    rubric_file = request.files['rubric']

    if not lab_report_file or not rubric_file:
        logger.error("No file uploaded")
        return jsonify({'error': 'PDF files are required.'}), 400

    lab_report_text = extract_text_from_pdf(lab_report_file)
    rubric_text = extract_text_from_pdf(rubric_file)

    logger.debug("Calling analyze_lab_report")
    analysis_result = analyze_lab_report(lab_report_text, rubric_text, student_name)
    logger.debug(f"Analysis result: {analysis_result}")
    doc_id = save_analysis_to_storage(student_name, lab_report_text, rubric_text, analysis_result)
    
    logger.debug("Returning response")
    return jsonify({
        'analysis_result': analysis_result,
        'doc_id': doc_id,
        'student_name': student_name,
        'lab_report': lab_report_text,
        'rubric': rubric_text
    })

@app.route('/get_lab_reports', methods=['GET'])
def get_lab_reports():
    logger.debug("Fetching lab reports")
    lab_reports_ref = db.collection('lab_reports')
    reports = lab_reports_ref.stream()
    
    if not reports:
        logger.warning("No lab reports found")
        return jsonify({'error': 'No lab reports found.'}), 404
    
    report_list = [report.to_dict() for report in reports]
    logger.debug("Returning lab reports")
    return jsonify(report_list)

@app.route('/submit_rating', methods=['POST'])
def submit_rating():
    logger.debug("Received rating submission")
    data = request.get_json()
    doc_id = data.get('doc_id')
    user_rating = data.get('user_rating')
    user_comments = data.get('user_comments')

    if not doc_id or user_rating is None:
        logger.error("Missing doc_id or user_rating")
        return jsonify({'error': 'Document ID and rating are required.'}), 400

    try:
        doc_ref = db.collection('lab_reports').document(doc_id)
        doc_ref.update({
            'user_rating': user_rating,
            'user_comments': user_comments
        })
        logger.debug(f"Updated doc {doc_id} with rating {user_rating} and comments: {user_comments}")
        return jsonify({'message': 'Rating and comments saved successfully'}), 200
    except Exception as e:
        logger.error(f"Error saving rating: {str(e)}")
        return jsonify({'error': f"Failed to save rating: {str(e)}"}), 500

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    logger.debug("Generating PDF for single entry")
    data = request.get_json()
    if not data:
        logger.error("No data provided for PDF generation")
        return jsonify({'error': 'No data provided.'}), 400

    student_name = data.get('student_name', 'Unknown')
    lab_report = data.get('lab_report', 'No report provided')
    rubric = data.get('rubric', 'No rubric provided')
    analysis_result = data.get('analysis_result', 'No feedback received')

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Lab Report Analysis", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Student Name: {student_name}", styles['Heading2']))
    story.append(Paragraph(f"Lab Report: {lab_report}", styles['BodyText']))
    story.append(Paragraph(f"Rubric: {rubric}", styles['BodyText']))
    story.append(Paragraph(f"Analysis Result: {analysis_result}", styles['BodyText']))
    story.append(Spacer(1, 12))

    doc.build(story)
    buffer.seek(0)
    
    logger.debug("PDF generated, sending for download")
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"lab_report_{student_name}.pdf",
        mimetype='application/pdf'
    )

if __name__ == '__main__':
    app.run(debug=True)