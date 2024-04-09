from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from werkzeug.utils import secure_filename
import os
from docx import Document
import pdfplumber
import logging

app = Flask(__name__)

# Configure MongoDB
app.config["MONGO_URI"] = "mongodb://localhost:27017/matchmaker"  # Update this URI as needed
mongo = PyMongo(app)

# Enable logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Configure the maximum upload size and the upload folder
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # For example, 16MB
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to process matching between job description and resume
def process_match(job_description, resume_text):
    job_description_words = set(job_description.lower().split())
    resume_words = set(resume_text.lower().split())
    matching_words = job_description_words.intersection(resume_words)
    
    logging.debug(f"Job Description Words: {job_description_words}")
    logging.debug(f"Resume Words: {resume_words}")
    logging.debug(f"Matching Words: {matching_words}")

    match_percentage = (len(matching_words) / len(job_description_words)) * 100 if job_description_words else 0
    missing_keywords = job_description_words - resume_words

    return match_percentage, list(missing_keywords)

@app.route('/')
def index():
    return "Welcome to the Resume Matchmaker App!"

@app.route('/upload', methods=['POST'])
def upload_file():
    # Start of the function body
    if 'resume' not in request.files:
        return jsonify(error="No resume part"), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify(error="No selected file"), 400
    if not allowed_file(file.filename):
        return jsonify(error="Invalid file type"), 400
    
    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)
    
    # Function now returns a JSON response indicating success
    return jsonify(message="File uploaded successfully", filename=filename)

@app.route('/match', methods=['POST'])
def match_resume_to_job_description():
    if 'jobDescription' not in request.form:
        return jsonify(error="Missing job description"), 400

    job_description = request.form['jobDescription']
    resume_text = ""

    if 'resume' in request.files:
        file = request.files['resume']
        if file.filename == '':
            return jsonify(error="No selected file"), 400
        if not allowed_file(file.filename):
            return jsonify(error="Invalid file type"), 400

        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)

        try:
            if filename.lower().endswith('.pdf'):
                with pdfplumber.open(save_path) as pdf:
                    pages = [page.extract_text() for page in pdf.pages if page.extract_text()]
                    resume_text = ' '.join(pages)
            elif filename.lower().endswith('.docx'):
                doc = docx.Document(save_path)
                resume_text = '\n'.join(paragraph.text for paragraph in doc.paragraphs)
            else:
                with open(save_path, 'r', encoding='utf-8', errors='ignore') as f:
                    resume_text = f.read()
        except Exception as e:
            return jsonify(error=str(e)), 500
    elif 'resume' in request.form:
        resume_text = request.form['resume']
    else:
        return jsonify(error="Missing resume"), 400

    match_percentage, missing_keywords = process_match(job_description, resume_text)
    
    mongo.db.match_results.insert_one({
        "job_description": job_description,
        "resume_text": resume_text,
        "match_percentage": match_percentage,
        "missing_keywords": missing_keywords
    })
    
    return jsonify({
        'matchPercentage': match_percentage,
        'missingKeywords': missing_keywords
    })


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        
    app.run(debug=True)
