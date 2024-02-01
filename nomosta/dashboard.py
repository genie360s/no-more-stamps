
import io
import qrcode
import base64
import os
from datetime import datetime
from io import BytesIO
from flask import (
    Blueprint, flash, redirect,g, render_template, request, url_for
)
from reportlab.pdfgen import canvas
from PyPDF2 import PdfWriter, PdfReader
from nomosta.auth import login_required
from nomosta.db import get_db
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image


import fitz 


ALLOWED_EXTENSIONS = {'pdf'}

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

def get_user_data():
    """returns all the necessary user data"""
    db = get_db()
    result_set = db.execute('''
        SELECT u.email, u.fullname, q.company_name, q.qr_code_image , q.phrase_word
        FROM user u
        JOIN qrcode q ON u.id = q.user_id;
    ''').fetchall()

    dash = []

    for row in result_set:
        data = dict(row)

        # Convert BLOB data to base64-encoded string
        if 'qr_code_image' in data:
            image_data = data['qr_code_image']
            if image_data:
                data['qr_code_image'] = f"data:image/png;base64,{base64.b64encode(image_data).decode('utf-8')}"
        print(data)
        dash.append(data)
    return dash

@bp.route('/dashboard')
@login_required
def dashboard():

    dash = get_user_data()

    return render_template('dashboard/dashboard.html', data=dash)



@bp.route('/generate_qr', methods=('GET','POST'))
@login_required
def generate_qr():
    error = None

    if request.method == 'POST':
        company_name = request.form['company_name']
        time_issued = request.form['time_issued']
        company_location = request.form['company_location']
        phrase_word = request.form['phrase_word']
        user_id = request.form['user_id']

        if not company_name:
            error = 'Company name is required.'
        elif not time_issued:
            error = 'Time issued is required.'
        elif not company_location:
            error = 'Company location is required.'
        elif not phrase_word:
            error = 'Phrase word is required.'
        elif not user_id:
            error = 'User ID is required.'

        if error is None:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=5
            )

            qr_code_info = [company_name, time_issued, company_location, phrase_word]
            data = '\n'.join(qr_code_info)
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            

            # Save QR code image to BytesIO
            img_bytes = BytesIO()
            img.save(img_bytes)
            img_bytes.seek(0)

            # Save QR code image to static folder
            #creating an absolute path to the static folder
            img_path = os.path.join(os.path.dirname(__file__), 'static', f'{company_name}.png')

            img.save(img_path)

            db = get_db()
            try:
                db.execute('INSERT INTO qrcode (company_name, time_issued, company_location, phrase_word, qr_code_image, user_id) VALUES (?, ?, ?, ?, ?, ?)',
                           (company_name, time_issued, company_location, phrase_word, img_bytes.read(), user_id))
                db.commit()
            except db.IntegrityError:
                error = f"QR Code '{company_name}' is already registered."
            else:
                return redirect(url_for('dashboard.dashboard'))

    flash(error)
    return render_template('dashboard/dashboard.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_upload(file_upload):
    """Validates the uploaded file and returns an error message if invalid."""
    if not file_upload:
        return 'No file selected.'
    elif not allowed_file(file_upload.filename):
        return 'Invalid file format. Allowed formats are: pdf'
    return None

def save_uploaded_file(file_upload):
    """Saves the uploaded file to the static/pdf_files folder and returns the path to the file."""
    pdf_directory = os.path.join(os.path.dirname(__file__), 'static/pdf_files')
    if not os.path.exists(pdf_directory):
        os.makedirs(pdf_directory)

    pdf_path = os.path.join(pdf_directory, secure_filename(file_upload.filename))
    file_upload.save(pdf_path)
    return pdf_path

def get_qr_code_image_data(company_name):
    """Returns the QR code image data for the given company name."""
    db = get_db()
    result_set = db.execute('SELECT qr_code_image FROM qrcode WHERE company_name = ?;', (company_name,)).fetchone()
    if not result_set:
        return None
    qrcode_data = dict(result_set)
    qrimage_data = qrcode_data['qr_code_image']
    qrpng_image = f"data:image/png;base64,{base64.b64encode(qrimage_data).decode('utf-8')}"
    return qrpng_image

def add_qr_code_to_pdf(pdf_path, qrpng_image):
    """ adds QR code to the PDF and returns the path to the output PDF file."""

    doc = fitz.open( f'{pdf_path}')

    output_folder = os.path.join(os.path.dirname(__file__), 'static/outpdf_files/')
    
    

    image_data = base64.b64decode(qrpng_image.split(',')[1])
    stream = io.BytesIO(image_data)

    for page in doc:
        w = page.rect.width  # width of this page
        margin = 20
        left = w - 240 - margin
        rect = fitz.Rect(left, margin, left + 240, margin + 240)  # top right square
        print(stream)
        page.insert_image(rect, stream=stream)
    new_pdf_path =  pdf_path.replace(".pdf", "_with_image.pdf")
    doc.save(new_pdf_path, deflate=True, garbage=3)
    doc.close()

    print(new_pdf_path)

    return new_pdf_path

def get_relative_pdf_path(full_pdf_path):
    """Returns the relative path for the given full path."""
    # Extract the file name from the full path
    file_name = os.path.basename(full_pdf_path)

    # Construct the relative path within the "/pdf_files/" directory
    relative_path = os.path.join("/pdf_files", file_name)

    return relative_path


@bp.route('/upload_pdf', methods=('GET', 'POST'))
@login_required
def upload_pdf():

    dash = get_user_data()

    if request.method == 'POST':
        file_upload = request.files.get('file_upload')
        selected_qrcode = request.form.get('selected_qrcode')

        file_error = validate_file_upload(file_upload)
        if not selected_qrcode:
            error = 'QR Code is required.'
            flash(error)
        elif file_error:
            flash(file_error)
        else:
            qrcode_image = get_qr_code_image_data(selected_qrcode)
            print(qrcode_image)

            # Save uploaded PDF file
            pdf_path = save_uploaded_file(file_upload)
            print(pdf_path)
            if pdf_path:
                # Add QR code to the PDF
                final_pdf = add_qr_code_to_pdf(pdf_path, qrcode_image)

                render_pdf = get_relative_pdf_path(final_pdf)

                if final_pdf:
                    print("Output PDF Path:", final_pdf)
                    dash = get_user_data()
                    return render_template('dashboard/dashboard.html', render_pdf = render_pdf, data = dash)

    return render_template('dashboard/dashboard.html', data=dash)

