# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'your_database_name'
}

# Application Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff'}

# OCR Configuration
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Update this path according to your Tesseract installation

# Application Settings
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
SECRET_KEY = 'your-secret-key-here'  # Change this to a secure secret key 