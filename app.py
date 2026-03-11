import os
import uuid
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.db')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

VALID_AGE_CATEGORIES = ['5-7', '8-10', '11-13', '14-17', '18-25', '26-35', '36-45', '46-55', '56-65', '66+']


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database and uploads folder."""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            age_category TEXT NOT NULL,
            image_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Render the data collection form."""
    return render_template('index.html', age_categories=VALID_AGE_CATEGORIES)


@app.route('/submit', methods=['POST'])
def submit():
    """Handle form submission."""
    # Validate consent
    consent = request.form.get('consent')
    if not consent:
        flash('You must agree to the consent statement before submitting.', 'error')
        return redirect(url_for('index'))

    # Validate age category
    age_category = request.form.get('age_category')
    if not age_category or age_category not in VALID_AGE_CATEGORIES:
        flash('Please select a valid age category.', 'error')
        return redirect(url_for('index'))

    # Validate image file
    if 'image' not in request.files:
        flash('Please upload a handwritten word image.', 'error')
        return redirect(url_for('index'))

    file = request.files['image']
    if file.filename == '':
        flash('No file selected. Please choose an image to upload.', 'error')
        return redirect(url_for('index'))

    if not allowed_file(file.filename):
        flash('Invalid file type. Only PNG, JPG, and JPEG images are accepted.', 'error')
        return redirect(url_for('index'))

    # Save file with random filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    random_filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], random_filename)
    file.save(filepath)

    # Store record in database
    conn = get_db()
    conn.execute(
        'INSERT INTO submissions (age_category, image_path, created_at) VALUES (?, ?, ?)',
        (age_category, random_filename, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    flash('Thank you! Your submission has been recorded successfully.', 'success')
    return redirect(url_for('index'))


@app.errorhandler(413)
def file_too_large(e):
    """Handle file size exceeding the limit."""
    flash('File is too large. Maximum allowed size is 5 MB.', 'error')
    return redirect(url_for('index'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
