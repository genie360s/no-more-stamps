import qrcode
import os
from io import BytesIO
from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)

from nomosta.auth import login_required
from nomosta.db import get_db

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    dash = db.execute(
        'SELECT user.id, user.fullname, user.username FROM user'
    ).fetchall()
    return render_template('dashboard/dashboard.html', dash=dash)

@bp.route('/generate_qr', methods=('GET','POST'))
@login_required
def generate_qr():
    error = None

    if request.method == 'POST':
        company_name = request.form['company_name']
        time_issued = request.form['time_issued']
        company_location = request.form['company_location']
        phrase_word = request.form['phrase_word']

        if not company_name:
            error = 'Company name is required.'
        elif not time_issued:
            error = 'Time issued is required.'
        elif not company_location:
            error = 'Company location is required.'
        elif not phrase_word:
            error = 'Phrase word is required.'

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
            img_path = os.path.join(os.path.dirname(__file__), 'qr_codes', f'{company_name}.png')

            img.save(img_path)

            db = get_db()
            try:
                db.execute('INSERT INTO qrcode (company_name, time_issued, company_location, phrase_word, qr_code_image) VALUES (?, ?, ?, ?, ?)',
                           (company_name, time_issued, company_location, phrase_word, img_bytes.read()))
                db.commit()
            except db.IntegrityError:
                error = f"QR Code '{company_name}' is already registered."
            else:
                return redirect(url_for('dashboard.dashboard'))

    flash(error)
    return render_template('dashboard/dashboard.html')
