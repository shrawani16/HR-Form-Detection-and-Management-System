import os
import pytesseract
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import mysql.connector
from PIL import Image
import fitz  # PyMuPDF
import re
import json
from datetime import datetime
from config import DB_CONFIG, UPLOAD_FOLDER, ALLOWED_EXTENSIONS

# Configure Flask App
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Create database if not exists
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
    cursor.execute(f"USE {DB_CONFIG['database']}")
    
    # Create documents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            upload_date DATETIME NOT NULL,
            extracted_data JSON,
            metadata JSON
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({"message": "No files provided"}), 400

    files = request.files.getlist('files')
    results = []
    
    for file in files:
        if file.filename == '':
            continue
            
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Process the file and extract all possible information
            extracted_data = process_file(filepath)
            metadata = {
                'file_type': file.content_type,
                'file_size': os.path.getsize(filepath),
                'processing_date': datetime.now().isoformat()
            }
            
            # Save to database
            save_to_database(filename, extracted_data, metadata)
            results.append({
                "filename": filename,
                "status": "success",
                "extracted_fields": len(extracted_data)
            })
        except Exception as e:
            results.append({
                "filename": filename,
                "status": "error",
                "message": str(e)
            })
        finally:
            # Clean up the uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
    
    return jsonify({"results": results})

def process_file(filepath):
    text = extract_text_from_file(filepath)
    return extract_all_information(text)

def extract_text_from_file(filepath):
    text = ""
    if filepath.lower().endswith('.pdf'):
        pdf_document = fitz.open(filepath)
        for page in pdf_document:
            text += page.get_text()
            # If no text found, use OCR
            if not text.strip():
                image = page.get_pixmap()
                img_path = "temp.png"
                image.save(img_path)
                text = pytesseract.image_to_string(Image.open(img_path))
                os.remove(img_path)
    elif filepath.lower().endswith(('.png', '.jpg', '.jpeg')):
        text = pytesseract.image_to_string(Image.open(filepath))
    return text

def extract_all_information(text):
    # Common patterns to look for
    patterns = {
        'email': r'[\w\.-]+@[\w\.-]+\.\w+',
        'phone': r'\+?[\d\s-]{10,}',
        'date': r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
        'url': r'https?://\S+',
        'pan': r'[A-Z]{5}[0-9]{4}[A-Z]{1}',
        'aadhar': r'\d{4}\s?\d{4}\s?\d{4}',
        'passport': r'[A-Z]{1}[0-9]{7}',
        'amount': r'₹?\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?',
        'percentage': r'\d{1,3}%',
        'time': r'\d{1,2}:\d{2}(?::\d{2})?\s?(?:AM|PM)?',
    }
    
    extracted_data = {}
    
    # Extract using patterns
    for key, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            extracted_data[key] = list(set(matches))
    
    # Extract potential key-value pairs
    lines = text.split('\n')
    for line in lines:
        if ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip().lower()
                value = parts[1].strip()
                if key and value:
                    extracted_data[key] = value
    
    # Extract potential section headers
    section_headers = re.findall(r'^[A-Z][A-Za-z\s]+:$', text, re.MULTILINE)
    if section_headers:
        extracted_data['sections'] = [h.strip(':') for h in section_headers]
    
    return extracted_data

def save_to_database(filename, extracted_data, metadata):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO documents (filename, extracted_data, metadata)
        VALUES (%s, %s, %s)
    ''', (filename, json.dumps(extracted_data), json.dumps(metadata)))
    
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/documents', methods=['GET'])
def get_documents():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('''
        SELECT id, filename, upload_date, extracted_data, metadata
        FROM documents
        ORDER BY upload_date DESC
    ''')
    
    documents = cursor.fetchall()
    result = []
    
    for doc in documents:
        result.append({
            'id': doc['id'],
            'filename': doc['filename'],
            'upload_date': doc['upload_date'].isoformat() if doc['upload_date'] else None,
            'extracted_data': json.loads(doc['extracted_data']),
            'metadata': json.loads(doc['metadata'])
        })
    
    cursor.close()
    conn.close()
    return jsonify(result)

@app.route('/search', methods=['GET'])
def search_documents():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('''
        SELECT id, filename, upload_date, extracted_data, metadata
        FROM documents
    ''')
    
    documents = cursor.fetchall()
    results = []
    
    for doc in documents:
        extracted_data = json.loads(doc['extracted_data'])
        # Search in all values
        for key, value in extracted_data.items():
            if isinstance(value, str) and query in value.lower():
                results.append({
                    'id': doc['id'],
                    'filename': doc['filename'],
                    'upload_date': doc['upload_date'].isoformat() if doc['upload_date'] else None,
                    'match': f"{key}: {value}"
                })
                break
            elif isinstance(value, list):
                for item in value:
                    if query in str(item).lower():
                        results.append({
                            'id': doc['id'],
                            'filename': doc['filename'],
                            'upload_date': doc['upload_date'].isoformat() if doc['upload_date'] else None,
                            'match': f"{key}: {item}"
                        })
                        break
    
    cursor.close()
    conn.close()
    return jsonify(results)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
