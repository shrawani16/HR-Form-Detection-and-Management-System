# HR Form Detection and Management System

A comprehensive system for processing and managing HR documents with intelligent text extraction capabilities.

## Features

- Support for multiple document formats (PDF, PNG, JPG, JPEG, TIFF)
- Intelligent text extraction using Tesseract OCR
- Flexible data storage in key-value format
- Secure file handling and database operations
- User-friendly web interface
- Search functionality for extracted data

## Prerequisites

- Python 3.8 or higher
- MySQL Server
- Tesseract OCR (for text extraction)
- Required Python packages (listed in requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Install Tesseract OCR:
   - Windows: Download and install from https://github.com/UB-Mannheim/tesseract/wiki
   - Linux: `sudo apt-get install tesseract-ocr`
   - macOS: `brew install tesseract`

5. Configure the application:
   - Copy `config.example.py` to `config.py`
   - Update the configuration settings in `config.py`:
     - Database credentials
     - Tesseract path
     - Upload folder location
     - Secret key

6. Initialize the database:
```bash
python init_db.py
```

## Usage

1. Start the application:
```bash
python server.py
```

2. Access the web interface at `http://localhost:5000`

3. Upload documents through the web interface

4. View and search extracted data

## Security Considerations

- Never commit `config.py` to version control
- Use strong passwords for database access
- Regularly update dependencies
- Implement proper access controls in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Database Setup

The system will automatically create the necessary database and table structure when first run. The table structure is:

```sql
CREATE TABLE IF NOT EXISTS documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extracted_data JSON,
    metadata JSON
);
```

## File Structure

- `server.py` - Main Flask application with MySQL integration
- `templates/index.html`
