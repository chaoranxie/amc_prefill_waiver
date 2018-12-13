import io
import logging
import os
import zipfile
from StringIO import StringIO

from aws_xray_sdk.core import patch_all, xray_recorder
from flask import Flask, flash, redirect, render_template, request, send_file

from flask_cors import CORS
from prefill_waiver import (chunk_size, generate_pdfs_data, get_all_participants, get_approved_participants,
                            get_leaders)

xray_recorder.configure(context_missing='LOG_ERROR')
patch_all()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']
CORS(app)

ALLOWED_EXTENSIONS = set(['csv'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api', methods=['POST'])
def api():
    file_stream = io.StringIO(request.json['csv'].encode('ascii', 'ignore').decode())
    date = request.json['date']
    return get_zip_from_stream(file_stream, date)


def get_zip_from_stream(file_stream, date):
    participants = get_all_participants(file_stream)
    leaders = get_leaders(participants)
    participants = get_approved_participants(participants)
    file_contents = generate_pdfs_data(
        waiver_pdf='static/waiver.pdf',
        approved_participants=participants,
        filled_waiver_base="filled_waiver_",
        chunk_size=chunk_size,
        leaders=leaders,
        date=date)
    in_memory = StringIO()
    zip = zipfile.ZipFile(in_memory, "a")
    for filename, content in file_contents.items():
        zip.writestr(filename, content)
    for file in zip.filelist:
        file.create_system = 0
    zip.close()
    in_memory.seek(0)
    response = send_file(in_memory, attachment_filename='filled_waivers.zip', as_attachment=True)
    return response


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            return get_zip_from_stream(file_stream=file.stream, date=None)
        else:
            flash('Invalid file')
            return redirect(request.url)

    return render_template('home.html')


if __name__ == '__main__':
    app.run()
